from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import stripe

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# STRIPE SETUP
# =========================
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# simple in-memory store (OK for MVP)
paid_tokens = set()

# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {"status": "running"}

# =========================
# ANALYZE (LOCKED)
# =========================
@app.get("/analyze")
def analyze(query: str, token: str = None):

    is_paid = token in paid_tokens

    results = [
        {"title": f"{query} system A", "abstract": "Patent example A", "similarity": 40},
        {"title": f"{query} system B", "abstract": "Patent example B", "similarity": 30},
        {"title": f"{query} system C", "abstract": "Patent example C", "similarity": 20}
    ]

    novelty = 70

    # 🔒 LOCKED VIEW FOR FREE USERS
    if not is_paid:
        results = [
            {"title": r["title"], "abstract": "🔒 Unlock to view full details", "similarity": None}
            for r in results
        ]

    return {
        "query": query,
        "novelty": novelty,
        "risk": "Medium",
        "paid": is_paid,
        "results": results
    }

# =========================
# CREATE CHECKOUT
# =========================
@app.post("/create-checkout")
def create_checkout():

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "product_data": {
                    "name": "PatentHound Full Report Access"
                },
                "unit_amount": 499,
            },
            "quantity": 1,
        }],
        success_url="https://patenthound.co.uk/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://patenthound.co.uk/cancel"
    )

    return {"url": session.url}

# =========================
# STRIPE SUCCESS CONFIRMATION
# =========================
@app.get("/verify-payment")
def verify_payment(session_id: str):

    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == "paid":
        token = str(uuid.uuid4())
        paid_tokens.add(token)
        return {"token": token}

    return {"error": "not paid"}
