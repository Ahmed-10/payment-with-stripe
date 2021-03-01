import stripe
from .db import Customer, Plans
import schedule
import time
from datetime import date
import os

def create_customer(user):
    stripe.api_key = os.environ['STRIPE_SECRET_KEY']
    try:
        customer = stripe.Customer.create(
            email=user['email'],
            name=user['company']
        )

        new_customer = Customer(
            customer['email'],
            customer['name'],
            user['id'],
            customer['id']
        )

        new_customer.insert()
        return {
            'message':'success',
        }
    except Exception as error:
        print(error)
        return {
            'message': str(error)
        }

def get_customer_plan(id):
    try:
        customer = Customer.query.filter_by(user_id=id).first()
        plan = Plans.query.get(customer.package)
        return {
            'plan': plan.plan_name
        }
    except Exception as error:
        print(error)
        return {
            'message': str(error)
        }

def calculate_subscription_amount(id):
    try:
        plan = Plans.query.get(int(id))
        return plan.price * 100
    except Exception as error:
        return str(error)

def force_subscription(user_id, plan_id):
    try:
        customer = Customer.query.filter_by(user_id=(user_id)).first()
        customer.package = int(plan_id)
        customer.renew_date = None
        customer.update()
        return {
            'message': 'success'
        }
    except Exception as error:
        print(error)
        return {
            'message': str(error)
        }

def charge_customer_off_session(id):
    customer = Customer.query.get(int(id))
    if(customer.off_session):
        try:
            # List the customer's payment methods to find one to charge
            stripe.api_key = os.environ['STRIPE_SECRET_KEY']
            payment_methods = stripe.PaymentMethod.list(
                customer=customer.stripe_id,
                type='card'
            )

            # Create and confirm a PaymentIntent with the
            # order amount, currency, Customer and PaymentMethod IDs
            # If authentication is required or the card is declined, Stripe
            # will throw an error
            intent = stripe.PaymentIntent.create(
                amount=calculate_subscription_amount(customer.package),
                currency=os.environ['currency'],
                payment_method=payment_methods['data'][0]['id'],
                customer=customer.stripe_id,
                confirm=True,
                off_session=True
            )

            return {
                'succeeded': True, 
            }
        except stripe.error.CardError as e:
            err = e.error
            if err.code == 'authentication_required':
                # Bring the customer back on-session to authenticate the purchase
                # You can do this by sending an email or app notification to let them know
                # the off-session purchase failed
                # Use the PM ID and client_secret to authenticate the purchase
                # without asking your customers to re-enter their details
                return {
                    'error': 'authentication_required', 
                    'paymentMethod': err.payment_method.id, 
                    'amount': calculate_subscription_amount(customer.package), 
                    'card': err.payment_method.card,
                    'clientSecret': err.payment_intent.client_secret
                }
            elif err.code:
                # The card was declined for other reasons (e.g. insufficient funds)
                # Bring the customer back on-session to ask them for a new payment method
                return {
                    'error': err.code, 
                }
    else:
        return {
            'message': "card isn't saved"
        }

def update_subscription():
    today = date.today()   
    customers = Customer.query.all()
    for customer in customers:
        if (customer.renew_date != None) and (today > customer.renew_date):
            response = charge_customer_off_session(customer.id)
            if 'succeeded' not in response:
                customer.package = 1
                customer.renew_date = None
                customer.update()

def update():
    schedule.every(2).seconds.do(update_subscription)

    while True:
        schedule.run_pending()
        time.sleep(1)

