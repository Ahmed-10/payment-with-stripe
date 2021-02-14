const stripe = Stripe('pk_test_51IJKWhBqrfVtgI4Xhxbt3ddvxQ0AhGQugIizWMS0Gfreh4mQqqAHuI576nZZgoTnihihU0GVox6l8eJwVCxMPeIV00Hv3641Vk');

const elements = stripe.elements();

// Set up Stripe.js and Elements to use in checkout form
const style = {
    base: {
        color: "#32325d",
        width: '50%',
        // lineHeight: '1.35',
        // color: "#495057",
        fontFamily: 'apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif',
        fontSmoothing: "antialiased",
        fontSize: "1.11rem",
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
    'placeholder': '',
    'style': style 
});
cardElement.mount('#card-element');

const form = document.getElementById('payment-form');

form.addEventListener('submit', async (event) => {
    // We don't want to let default form submission happen here,
    // which would refresh the page.
    event.preventDefault();

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
        console.log(response.error)
    } else if (response.requires_action) {
        // Use Stripe.js to handle the required card action
        const { error: errorAction, paymentIntent } =
            await stripe.handleCardAction(response.payment_intent_client_secret);

        if (errorAction) {
            // Show error from Stripe.js in payment form
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
        console.log(response)
    }
}
