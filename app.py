import os
import stripe
from flask import Flask, Blueprint, jsonify, render_template, request
from flask_restful import Api


#create the app
app = Flask(__name__)

# restful
api_bp = Blueprint('api', __name__)
api = Api(api_bp, prefix="/api")

stripe_keys = {
    "secret_key": os.environ["SECRET_KEY"],
    "publishable_key": os.environ["PUBLISHABLE_KEY"],
    "endpoint_secret": os.environ["ENDPOINT_SECRET"]
}
 
stripe.api_key = stripe_keys["secret_key"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/config")
def get_publishable_key():
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)


@app.route("/create-checkout-session")
def create_checkout_session():
    domain_url = "http://127.0.0.1:5000/"
    stripe.api_key = stripe_keys["secret_key"]

    try:
        # Create new Checkout Session for the order
        # Other optional params include:
        # [billing_address_collection] - to display billing address details on the page
        # [customer] - if you have an existing Stripe Customer ID
        # [payment_intent_data] - capture the payment later
        # [customer_email] - prefill the email input in the form
        # For full details see https://stripe.com/docs/api/checkout/sessions/create

        # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "cancelled",
            payment_method_types=["card"],
            mode="payment",     
            line_items=[{
                'price_data':{
                    'currency': 'usd',
                    'unit_amount': 20,
                    'product_data': {
                        'name': 'Brigadeiro',
                        'description': 'Brigadeiro Tradicional',
                        'images': ['https://img.freepik.com/fotos-premium/brigadeiro-brasileiro-tradicional-isolado-na-superficie-branca_70216-349.jpg'],
                    },
                },
                'quantity': 1
            }],
        )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/cancelled")
def cancelled():
    return render_template("cancelled.html")

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_keys["endpoint_secret"]
        )

    except ValueError as e:
        # Invalid payload
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return "Invalid signature", 400

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        print("Payment was successful.")
        # TODO: run some custom code here

    return "Success", 200

if __name__ == '__main__':
    app.run(debug=True)