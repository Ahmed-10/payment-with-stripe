// INTEGRATION NOTE #5: cupdate stripe configeration
const stripe = Stripe('pk_test_51IJKWhBqrfVtgI4Xhxbt3ddvxQ0AhGQugIizWMS0Gfreh4mQqqAHuI576nZZgoTnihihU0GVox6l8eJwVCxMPeIV00Hv3641Vk');

const elements = stripe.elements();
const style = {
base: {
    color: "#32325d",
    fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
    fontSmoothing: "antialiased",
    fontSize: "16px",
    "::placeholder": {
    color: "#aab7c4"
    }
},
invalid: {
    color: "#fa755a",
    iconColor: "#fa755a"
}
};

const card = elements.create("card", { style: style });
card.mount("#card-element");

document.querySelector("#submit").addEventListener("click", function(evt) {
    evt.preventDefault();
    pay(stripe, card);
});

const handleAction = function(clientSecret) {
  // Show the authentication modal if the PaymentIntent has a status of "requires_action"
  stripe.handleCardAction(clientSecret).then(function(data) {
    if (data.error) {
      showError("Your card was not authenticated, please try again");
    } else if (data.paymentIntent.status === "requires_confirmation") {
      // Card was properly authenticated, we can attempt to confirm the payment again with the same PaymentIntent
      fetch("/subscripe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          paymentIntentId: data.paymentIntent.id,
          customer: customer,
          plan: plan
        })
      })
        .then(function(result) {
          return result.json();
        })
        .then(function(json) {
          if (json.error) {
            showError(json.error);
          } else {
            orderComplete(clientSecret);
          }
        });
    }
  });
};

/*
 * Collect card details and pay for the order 
 */
const pay = function(stripe, card) {
  let orderData = {}  
  changeLoadingState(true);
  // Collect card details
  stripe
    .createPaymentMethod("card", card)
    .then(function(result) {
      if (result.error) {
        showError(result.error.message);
      } else {
        orderData.paymentMethodId = result.paymentMethod.id;
        orderData.isSavingCard = document.querySelector("#save-card").checked;
        orderData.customer = customer;
        orderData.plan = plan;
        return fetch("/subscripe", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(orderData)
        });
      }
    })
    .then(function(result) {
      return result.json();
    })
    .then(function(paymentData) {
      if (paymentData.requiresAction) {
        // Request authentication
        handleAction(paymentData.clientSecret);
      } else if (paymentData.error) {
        showError(paymentData.error);
      } else {
        orderComplete(paymentData.clientSecret);
      }
    });
};

/* ------- Post-payment helpers ------- */

/* Shows a success / error message when the payment is complete */
const orderComplete = function(clientSecret) {
  stripe.retrievePaymentIntent(clientSecret).then(function(result) {
    const paymentIntent = result.paymentIntent;
    const paymentIntentJson = JSON.stringify(paymentIntent, null, 2);
    document.querySelectorAll(".payment-view").forEach(function(view) {
      view.classList.add("hidden");
    });
    document.querySelectorAll(".completed-view").forEach(function(view) {
      view.classList.remove("hidden");
    });
    document.querySelector(".status").textContent =
      paymentIntent.status === "succeeded" ? "succeeded" : "failed";
    const transaction = JSON.parse(paymentIntentJson)
    document.querySelector("pre").textContent = JSON.stringify({
      transaction_id: transaction.id,
      amount: `$${transaction.amount / 100} ${transaction.currency.toUpperCase()}`
    }, null, 2);
  });
};

const showError = function(errorMsgText) {
  changeLoadingState(false);
  const errorMsg = document.querySelector(".sr-field-error");
  errorMsg.textContent = errorMsgText;
  setTimeout(function() {
    errorMsg.textContent = "";
  }, 10000);
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