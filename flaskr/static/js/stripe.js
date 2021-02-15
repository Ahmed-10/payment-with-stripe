const stripe = Stripe('pk_test_51IJKWhBqrfVtgI4Xhxbt3ddvxQ0AhGQugIizWMS0Gfreh4mQqqAHuI576nZZgoTnihihU0GVox6l8eJwVCxMPeIV00Hv3641Vk');

const elements = stripe.elements();

// Set up Stripe.js and Elements to use in checkout form
const style = {
    base: {
        color: "#32325d",
        fontFamily: 'apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
        fontSmoothing: "antialiased",
        "::placeholder": {
            color: "#aab7c4"
        }
    },
    invalid: {
        color: "#fa755a",
        iconColor: "#fa755a"
    },
};

const cardElement = elements.create('card', { 
    'style': style,
    'hidePostalCode': true,
});
cardElement.mount('#card-element');
cardElement.on('change', function(event) {
    changeBtnState(event.complete)
});

const form = document.getElementById('payment-form');

form.addEventListener('submit', async (event) => {
    // We don't want to let default form submission happen here,
    // which would refresh the page.
    event.preventDefault();
    changeLoadingState(true);
    const result = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
        billing_details: {
            // Include any additional collected billing details.
            name: 'Jenny Rosen',
        },
    })

    stripePaymentMethodHandler(result);
});

const stripePaymentMethodHandler = async (result) => {
    if (result.error) {
        // Show error in payment form
        showError(result.error)
    } else {
        // Otherwise send paymentMethod.id to your server (see Step 4)
        const res = await fetch(`${ window.origin }/pay`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                payment_method_id: result.paymentMethod.id,
            }),
        })
        const paymentResponse = await res.json();
        // Handle server response (see Step 4)
        handleServerResponse(paymentResponse);
    }
}

const handleServerResponse = async (response) => {
    if (response.error) {
        // Show error from server on payment form
        showError(response.error)
    } else if (response.requires_action) {
        // Use Stripe.js to handle the required card action
        const { error: errorAction, paymentIntent } =
            await stripe.handleCardAction(response.payment_intent_client_secret);

        if (errorAction) {
            // Show error from Stripe.js in payment form
            console.log(errorAction)
            showError(errorAction.message)
        } else {
            // The card action has been handled
            // The PaymentIntent can be confirmed again on the server
            const serverResponse = await fetch('/pay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ payment_intent_id: paymentIntent.id })
            });
            handleServerResponse(await serverResponse.json());
        }
    } else {
        // Show success message
        orderComplete(response)
    }
}


/* ------- Post-payment helpers ------- */

/* Shows a success / error message when the payment is complete */
const orderComplete = function(response) {
    const responseJson = JSON.stringify(response, null, 2);
    document.querySelector(".sr-payment-form").classList.add("hidden");
    document.querySelector("pre").textContent = responseJson;

    document.querySelector(".sr-result").classList.remove("hidden");
    setTimeout(function() {
    document.querySelector(".sr-result").classList.add("expand");
    }, 200);

    changeLoadingState(false);
  };
  
  const showError = function(errorMsgText) {
    changeLoadingState(false);
    const errorMsg = document.querySelector(".sr-field-error");
    errorMsg.textContent = errorMsgText.message;
    setTimeout(function() {
      errorMsg.textContent = "";
    }, 4000);
  };
  

// Show a spinner on payment submission
const changeLoadingState = function(isLoading) {
    if (isLoading) {
      document.querySelector("button").disabled = true;
      document.querySelector("#spinner").classList.remove("hidden");
      document.querySelector("#button-text").classList.add("hidden");
    } else {
      document.querySelector("button").disabled = false;
      document.querySelector("#spinner").classList.add("hidden");
      document.querySelector("#button-text").classList.remove("hidden");
    }
};

const changeBtnState = function(isComplete) {
    const btn = document.getElementById('submit')
    if(isComplete){
        btn.disabled = false;
    } else {
        btn.disabled = true;
    }
}