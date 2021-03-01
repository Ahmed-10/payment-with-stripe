from flaskr import app
from flask import render_template, request, jsonify
import stripe
import json
from .db import Customer, Plans
from .subscription import calculate_subscription_amount
from datetime import date
import os

features = [
    'a.Aida dere',
    'b.Nec feugiat nisl',
    'c.Nulla at volutpat dola',
    'd.Pharetra massa',
    'e.Massa ultricies mi'
]

@app.route('/customers/<id>/plans')
def subsciption_plans(id):
    # get user data and pricing plan from the database
    customer = Customer.query.filter_by(user_id=int(id)).first()
    _plans = Plans.query.all()
    plans = [plan.format() for plan in _plans] 
    return render_template(
        'subscription/pricing-plans.html', 
        customer=customer.format(), 
        plans=plans,
        features=[feature.split('.')[1] for feature in features],
        logo=os.environ['logo']
    )


@app.route('/customers/<id>/plans/<plan_id>/')
def get_subscripe(id, plan_id):
    customer = Customer.query.filter_by(user_id=int(id)).first()
    if(customer.package == int(plan_id)):
        return "you are subscriped to this plan_id"
    elif plan_id == '1':
        return "you want to un-subscripe"
    else:
        plan = Plans.query.get(int(plan_id))
        # customer = customer.format()
        # customer['new_plan'] = plan_id
        return render_template(
            'subscription/checkout.html', 
            customer=customer.format(), 
            plan=plan.format()
        )


@app.route('/subscripe', methods=['POST'])
def subscripe():
  data = json.loads(request.data)
  customer = data['customer']
  plan = data['plan']
  try:
    stripe.api_key = os.environ['STRIPE_SECRET_KEY']
    if "paymentIntentId" not in data:
        payment_intent_data = dict(
            amount=calculate_subscription_amount(plan['id']),
            currency= os.environ['currency'],
            payment_method=data['paymentMethodId'],
            confirmation_method='manual',
            confirm=True
        )

        if data['isSavingCard']:
            # Create a Customer to store the PaymentMethod for reuse
            payment_intent_data['customer'] = customer['stripe_id']
            # setup_future_usage saves the card and tells Stripe how you plan to use it later
            # set to 'off_session' if you plan on charging the saved card when the customer is not present
            payment_intent_data['setup_future_usage'] = 'off_session'

            customer_data = Customer.query.get(customer['id'])
            customer_data.off_session = True
            customer_data.update()

        # Create a new PaymentIntent for the order
        intent = stripe.PaymentIntent.create(**payment_intent_data)
    else:
        # Confirm the PaymentIntent to collect the money
        intent = stripe.PaymentIntent.confirm(data['paymentIntentId'])
    return generate_response(intent, customer, plan)
  except Exception as e:
    return jsonify(error=str(e)), 403


def generate_response(intent, customer, plan):
    status = intent['status']
    if status == 'requires_action' or status == 'requires_source_action':
        # Card requires authentication
        return jsonify({'requiresAction': True, 'paymentIntentId': intent['id'], 'clientSecret': intent['client_secret']})
    elif status == 'requires_payment_method' or status == 'requires_source':
        # Card was not properly authenticated, suggest a new payment method
        return jsonify({'error': 'Your card was denied, please provide a new payment method'})
    elif status == 'succeeded':
        # Payment is complete, authentication not required
        # To cancel the payment after capture you will need to issue a Refund (https://stripe.com/docs/api/refunds)
        print("💰 Payment received!")

        customer_update = Customer.query.get(int(customer['id']))
        customer_update.package = int(plan['id'])    
        customer_update.renew_date = date.today()  
        customer_update.update()
        return jsonify({'clientSecret': intent['client_secret']})


@app.route('/plans')
def get_plans():
    _plans = Plans.query.all()
    plans = [plan.format() for plan in _plans]
    return render_template('subscription/plans-form.html', plans=plans, features=features)


@app.route('/plans/<id>')
def get_plan(id):
    plan = Plans.query.get(int(id))
    return render_template('subscription/plan.html', plan=plan.format())


@app.route('/plans', methods=['POST'])
def add_plan():
    data = request.get_json()
    plan = Plans(
        data['plan_name'],
        data['price'],
        data['features']
    )

    plan.insert()
    return jsonify({
        'plan': plan.format(),
        'message': 'success'
    })


# @app.route('/plans/<id>', methods=['PATCH'])
# def edit_plan(id):
#     plan = Plans.query.get(int(id))
#     pass


@app.route('/plans/<id>', methods=['DELETE'])
def delete_plan(id):
    if id == '1':
        pass
    else:
        plan = Plans.query.get(int(id))
        plan.delete()
        return jsonify({ 'message': 'ok' })