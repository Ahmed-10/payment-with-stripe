from flask import Flask, render_template, request
from flask_cors import CORS
import json
import stripe

app = Flask(__name__)
CORS(app)
app.config['STRIPE_SECRET_KEY'] = 'sk_test_51IJKWhBqrfVtgI4XstKyjdhhiUILSh6fLvQk2happe2XGhJqWF3wnxe9E2E7xQZ6HUFbrYcrhqzRZz7r8DWKU0zi00U8vZXHVU'
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
        payment_method = data['payment_method_id'],
        amount = 2000,
        currency = 'gbp',
        confirmation_method = 'manual',
        confirm = True,
      )
    elif 'payment_intent_id' in data:
      intent = stripe.PaymentIntent.confirm(data['payment_intent_id'])
  except stripe.error.CardError as e:
    # Display error on client
    return json.dumps({'error': e.user_message}), 200

  return generate_response(intent)

def generate_response(intent):
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


if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8000, debug=True)
 