from re import search
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from jinja2.utils import consume
import stripe

app = Flask(__name__)
CORS(app)
app.config['STRIPE_SECRET_KEY'] = 'sk_test_51IJKWhBqrfVtgI4XstKyjdhhiUILSh6fLvQk2happe2XGhJqWF3wnxe9E2E7xQZ6HUFbrYcrhqzRZz7r8DWKU0zi00U8vZXHVU'
app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_51IJKWhBqrfVtgI4Xhxbt3ddvxQ0AhGQugIizWMS0Gfreh4mQqqAHuI576nZZgoTnihihU0GVox6l8eJwVCxMPeIV00Hv3641Vk'
app.config['CUSTOMER_ID'] = ''
@app.route('/')
def index():
    return render_template('payment-form.html')

# AJAX endpoint when `/pay` is called from client


@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    intent = None

    try:
        if 'payment_method_id' in data:
            # Create the PaymentIntent
            stripe.api_key = app.config['STRIPE_SECRET_KEY']
            intent = stripe.PaymentIntent.create(
              payment_method=data['payment_method_id'],
              amount=2000,
              currency='gbp',
              confirmation_method='manual',
              confirm=True,
            )
        elif 'payment_intent_id' in data:
            intent = stripe.PaymentIntent.confirm(data['payment_intent_id'])
    except stripe.error.CardError as e:
        # Display error on client
        return json.dumps({'error': e.user_message}), 200

    return generate_response_card(intent)


def generate_response_card(intent):
    # Note that if your API version is before 2019-02-11, 'requires_action'
    # appears as 'requires_source_action'.
    if intent.status == 'requires_action' and intent.next_action.type == 'use_stripe_sdk':
        # Tell the client to handle the action
        return json.dumps({
          'requires_action': True,
          'payment_intent_client_secret': intent.client_secret,
        }), 200
    elif intent.status == 'succeeded':
        # The payment didn’t need any additional actions and completed!
        # Handle post-payment fulfillment
        return json.dumps({
          'success': True,
          'amount': 2000,
          'currency': 'gbp',
        }), 200
    else:
        # Invalid status
        return json.dumps({'error': 'Invalid PaymentIntent status'}), 500


@app.route('/stripe-key', methods=['GET'])
def fetch_key():
    # Send publishable key to client
    return jsonify({'publicKey': app.config['STRIPE_PUBLIC_KEY']})


@app.route('/subscripe')
def get_subscripe():
  return render_template('subscription.html')

@app.route('/subscripe', methods=['POST'])
def subscripe():
  data = json.loads(request.data)
  try:
    stripe.api_key = app.config['STRIPE_SECRET_KEY']
    if "paymentIntentId" not in data:
        payment_intent_data = dict(
            amount=3000,
            currency='gbp',
            payment_method=data['paymentMethodId'],
            confirmation_method='manual',
            confirm=True
        )

        if data['isSavingCard']:
            # Create a Customer to store the PaymentMethod for reuse
            customer = stripe.Customer.create()
            payment_intent_data['customer'] = customer['id']
            app.config['CUSTOMER_ID'] = customer['id']
            # setup_future_usage saves the card and tells Stripe how you plan to use it later
            # set to 'off_session' if you plan on charging the saved card when the customer is not present
            payment_intent_data['setup_future_usage'] = 'off_session'

        # Create a new PaymentIntent for the order
        intent = stripe.PaymentIntent.create(**payment_intent_data)
    else:
        # Confirm the PaymentIntent to collect the money
        intent = stripe.PaymentIntent.confirm(data['paymentIntentId'])
    return generate_response(intent)
  except Exception as e:
    return jsonify(error=str(e)), 403


def generate_response(intent):
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
        return jsonify({'clientSecret': intent['client_secret']})


@app.route('/charge-card-off-session')
def create_payment():
    try:
        # List the customer's payment methods to find one to charge
        payment_methods = stripe.PaymentMethod.list(
            customer=app.config['CUSTOMER_ID'],
            type='card'
        )

        # Create and confirm a PaymentIntent with the
        # order amount, currency, Customer and PaymentMethod IDs
        # If authentication is required or the card is declined, Stripe
        # will throw an error
        intent = stripe.PaymentIntent.create(
            amount=3000,
            currency='gbp',
            payment_method=payment_methods['data'][0]['id'],
            customer=app.config['CUSTOMER_ID'],
            confirm=True,
            off_session=True
        )

        return jsonify({
            'succeeded': True, 
            'publicKey': app.config['STRIPE_PUBLIC_KEY'], 
            'clientSecret': intent.client_secret
        })
    except stripe.error.CardError as e:
        err = e.error
        if err.code == 'authentication_required':
            # Bring the customer back on-session to authenticate the purchase
            # You can do this by sending an email or app notification to let them know
            # the off-session purchase failed
            # Use the PM ID and client_secret to authenticate the purchase
            # without asking your customers to re-enter their details
            return jsonify({
                'error': 'authentication_required', 
                'paymentMethod': err.payment_method.id, 
                'amount': 3000, 
                'card': err.payment_method.card, 
                'publicKey': app.config['STRIPE_PUBLIC_KEY'], 
                'clientSecret': err.payment_intent.client_secret
            })
        elif err.code:
            # The card was declined for other reasons (e.g. insufficient funds)
            # Bring the customer back on-session to ask them for a new payment method
            return jsonify({
                'error': err.code, 
                'publicKey': app.config['STRIPE_PUBLIC_KEY'], 
                'clientSecret': err.payment_intent.client_secret
            })


@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
