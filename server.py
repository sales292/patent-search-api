# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import uuid
import stripe
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Simple in-memory token store
paid_tokens = set()

# ---------- Home ----------
@app.get("/")
def home():
    return {"status": "running"}

# ---------- Analyze ----------
@app.get("/analyze")
def analyze(query: str, token: str = None):
    is_paid = token in paid_tokens

    results = [
        {"title": f"{query} system A", "abstract": "Patent example A", "similarity": 40},
        {"title": f"{query} system B", "abstract": "Patent example B", "similarity": 30},
        {"title": f"{query} system C", "abstract": "Patent example C", "similarity": 20},
    ]

    novelty = 70

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

# ---------- Create Checkout ----------
@app.post("/create-checkout")
def create_checkout():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": "PatentHound Full Report Access"},
                "unit_amount": 499,
            },
            "quantity": 1,
        }],
        success_url="https://patenthound.co.uk/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://patenthound.co.uk/cancel"
    )
    return {"url": session.url}

# ---------- Verify Payment ----------
@app.get("/verify-payment")
def verify_payment(session_id: str):
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status == "paid":
        token = str(uuid.uuid4())
        paid_tokens.add(token)
        return {"token": token}
    return {"error": "not paid"}

# ---------- Download PDF ----------
@app.get("/download-pdf")
def download_pdf(query: str, token: str = None):
    is_paid = token in paid_tokens
    if not is_paid:
        return {"error": "Payment required"}

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    # Header
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"PatentHound Report: {query}")

    y -= 40
    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Novelty Score: 70/100")
    y -= 20
    p.drawString(50, y, "Risk Level: Medium")
    y -= 40
    p.drawString(50, y, "Similar Patents:")

    sample_results = [
        "Patent A - bicycle brake system",
        "Patent B - braking mechanism",
        "Patent C - hydraulic control system"
    ]
    y -= 20
    for r in sample_results:
        if y < 80:
            p.showPage()
            y = height - 50
        p.drawString(50, y, r)
        y -= 20

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"}
    )
