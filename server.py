from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import stripe
import uuid

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
stripestripe.api_key = os.getenv("STRIPE_SECRET_KEY")

paid_users = set()

# =========================
# HOME TEST
# =========================
@app.get("/")
def home():
    return {"status": "running"}

# =========================
# ANALYZE (FREE ONLY FOR NOW)
# =========================
@app.get("/analyze")
def analyze(query: str):

    results = [
        {"title": f"{query} system A", "abstract": "Test patent A", "similarity": 40},
        {"title": f"{query} system B", "abstract": "Test patent B", "similarity": 30},
        {"title": f"{query} system C", "abstract": "Test patent C", "similarity": 20}
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
        success_url="https://patenthound.co.uk/success",
        cancel_url="https://patenthound.co.uk"
    )

    return {"url": session.url}
