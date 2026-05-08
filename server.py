from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import uuid
import stripe
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = FastAPI()

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Stripe
# -----------------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# TEMP MVP storage (replace with DB later)
paid_sessions = set()

# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/")
def home():
    return {"status": "running"}

# -----------------------------
# ANALYZE ENDPOINT
# -----------------------------
@app.get("/analyze")
def analyze(query: str, session_id: str = None):

    is_paid = session_id in paid_sessions

    results = [
        {"title": f"{query} system A", "abstract": "Patent example A", "similarity": 42},
        {"title": f"{query} system B", "abstract": "Patent example B", "similarity": 31},
        {"title": f"{query} system C", "abstract": "Patent example C", "similarity": 18},
    ]

    novelty = 70

    # lock details if not paid
    if not is_paid:
        results = [
            {
                "title": r["title"],
                "abstract": "🔒 Unlock full patent details",
                "similarity": None
            }
            for r in results
        ]

    return {
        "query": query,
        "novelty": novelty,
        "risk": "Medium",
        "paid": is_paid,
        "results": results
    }

# -----------------------------
# STRIPE CHECKOUT
# -----------------------------
@app.post("/create-checkout")
def create_checkout():

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
            success_url="https://patenthound.co.uk/subscription?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://patenthound.co.uk/cancel"
        )

        return {"url": session.url}

    except Exception as e:
        print("Stripe error:", str(e))
        return {"error": str(e)}

# -----------------------------
# STRIPE WEBHOOK (CORE SaaS LOGIC)
# -----------------------------
@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):

    payload = await request.body()
    event = None

    try:
        event = json.loads(payload)
    except Exception as e:
        print("Webhook parse error:", str(e))
        return {"status": "invalid"}

    if event.get("type") == "checkout.session.completed":

        session = event["data"]["object"]
        session_id = session.get("id")

        print("PAYMENT SUCCESS:", session_id)

        if session_id:
            paid_sessions.add(session_id)

    return {"status": "success"}

# -----------------------------
# PDF DOWNLOAD (PROTECTED)
# -----------------------------
@app.get("/download-pdf")
def download_pdf(query: str, session_id: str = None):

    if session_id not in paid_sessions:
        return {"error": "Payment required"}

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"PatentHound Report: {query}")

    y -= 40
    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Novelty Score: 70/100")
    y -= 20
    p.drawString(50, y, "Risk Level: Medium")

    y -= 40
    p.drawString(50, y, "Similar Patents:")

    sample = [
        "Patent A - system design",
        "Patent B - mechanical structure",
        "Patent C - control method"
    ]

    y -= 20
    for item in sample:
        if y < 80:
            p.showPage()
            y = height - 60
        p.drawString(50, y, item)
        y -= 20

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"}
    )
