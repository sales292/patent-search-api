from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import stripe
import uuid

app = FastAPI()

# allow frontend access
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
stripe.api_key = "https://buy.stripe.com/test_3cI28teFP3MCcum4GZ6Na00"

# temporary session store (upgrade to DB later)
paid_sessions = {}

# =========================
# ANALYZE (FREE + PAID)
# =========================
@app.get("/analyze")
def analyze(query: str, token: str = None):

    # MOCK "PATENT ENGINE" (replace later with real API)
    base_results = [
        {"title": f"{query} system A", "abstract": "Example patent A", "similarity": 45},
        {"title": f"{query} system B", "abstract": "Example patent B", "similarity": 30},
        {"title": f"{query} system C", "abstract": "Example patent C", "similarity": 20}
    ]

    avg = sum(r["similarity"] for r in base_results) / len(base_results)
    novelty = round(100 - avg)

    preview = {
        "novelty": novelty,
        "risk": "Medium" if avg > 30 else "Low",
        "results": [
            base_results[0],  # FREE preview only 1 result
            {"locked": True},
            {"locked": True}
        ],
        "paid": False
    }

    # FREE USERS
    if not token or token not in paid_sessions:
        return preview

    # PAID USERS (FULL ACCESS)
    return {
        "novelty": novelty,
        "risk": "High" if avg > 60 else "Medium",
        "results": base_results,
        "paid": True,
        "pdf_enabled": True
    }

# =========================
# CREATE STRIPE CHECKOUT
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
                    "name": "PatentHound Full Report"
                },
                "unit_amount": 499,
            },
            "quantity": 1,
        }],
        success_url="https://patenthound.co.uk/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://patenthound.co.uk"
    )

    return {"url": session.url}

# =========================
# STRIPE WEBHOOK (SECURITY CORE)
# =========================
@app.post("/webhook")
async def webhook(request: Request):

    payload = await request.json()

    if payload["type"] == "checkout.session.completed":

        token = str(uuid.uuid4())

        paid_sessions[token] = {
            "paid": True
        }

        print("PAYMENT SUCCESS TOKEN:", token)

    return {"status": "ok"}

# =========================
# OPTIONAL: VERIFY TOKEN
# =========================
@app.get("/verify")
def verify(token: str):
    return {"valid": token in paid_sessions}
