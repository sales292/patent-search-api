from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# =========================
# CORS (allow frontend)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# STRIPE (SAFE INIT)
# =========================
stripe = None
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY")

if STRIPE_KEY:
    try:
        import stripe as stripe_lib
        stripe_lib.api_key = STRIPE_KEY
        stripe = stripe_lib
        print("Stripe loaded")
    except Exception as e:
        print("Stripe failed:", e)
else:
    print("Stripe not configured (safe mode)")

# =========================
# HOME TEST
# =========================
@app.get("/")
def home():
    return {"status": "running"}

# =========================
# ANALYZER
# =========================
@app.get("/analyze")
def analyze(query: str):

    results = [
        {"title": f"{query} system A", "abstract": "Patent example A", "similarity": 40},
        {"title": f"{query} system B", "abstract": "Patent example B", "similarity": 30},
        {"title": f"{query} system C", "abstract": "Patent example C", "similarity": 20}
    ]

    avg = sum(r["similarity"] for r in results) / len(results)
    novelty = round(100 - avg)

    return {
        "query": query,
        "novelty": novelty,
        "risk": "Medium",
        "results": results,
        "paid": False
    }

# =========================
# STRIPE CHECKOUT
# =========================
@app.post("/create-checkout")
def create_checkout():

    if stripe is None:
        return {"error": "Stripe not configured"}

    try:
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
            success_url="https://patenthound.co.uk/success",
            cancel_url="https://patenthound.co.uk/cancel"
        )

        return {"url": session.url}

    except Exception as e:
        return {"error": str(e)}
