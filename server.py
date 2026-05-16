from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import stripe
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from datetime import datetime

app = FastAPI()

# =====================================================
# CORS
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# STRIPE
# =====================================================
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

paid_sessions = set()

# =====================================================
# HOME
# =====================================================
@app.get("/")
def home():
    return {"status": "ok"}

# =====================================================
# SIMPLE "AI" SCORE ENGINE (replace later with real model)
# =====================================================
def generate_scores(query: str):
    base = abs(hash(query)) % 60 + 20  # deterministic-ish 20–80

    return [
        {
            "title": f"{query} mechanical system",
            "abstract": "Relevant mechanical control architecture with partial overlap.",
            "similarity": min(95, base + 10),
        },
        {
            "title": f"{query} hydraulic mechanism",
            "abstract": "Hydraulic implementation with functional similarity.",
            "similarity": min(95, base),
        },
        {
            "title": f"{query} safety automation system",
            "abstract": "Automation logic with partial conceptual overlap.",
            "similarity": max(10, base - 15),
        }
    ]

# =====================================================
# ANALYZE
# =====================================================
@app.get("/analyze")
def analyze(query: str, session_id: str = None):

    is_paid = session_id in paid_sessions

    results = generate_scores(query)

    # IMPORTANT: NEVER NULL OUT SCORES (this was breaking UI)
    for r in results:
        r["locked"] = not is_paid

        if not is_paid:
            r["abstract"] = "🔒 Unlock full details"
            r["url"] = None
        else:
            r["url"] = f"https://patents.google.com/?q={query}"

    novelty = max(10, min(95, 100 - sum(r["similarity"] for r in results) // 3))
    risk = "Low" if novelty > 70 else "Medium" if novelty > 40 else "High"

    return {
        "query": query,
        "paid": is_paid,
        "novelty": novelty,
        "risk": risk,
        "results": results
    }

# =====================================================
# STRIPE CHECKOUT
# =====================================================
@app.post("/create-checkout")
def create_checkout():

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": "PatentHound Full Report"},
                "unit_amount": 899,
            },
            "quantity": 1,
        }],
        success_url="https://patenthound.co.uk/patent-analyzer?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://patenthound.co.uk/patent-analyzer"
    )

    return {"url": session.url}

# =====================================================
# WEBHOOK
# =====================================================
@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):

    payload = await request.body()

    try:
        event = json.loads(payload)
    except:
        return {"status": "invalid"}

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")

        if session_id:
            paid_sessions.add(session_id)
            print("PAYMENT SUCCESS:", session_id)

    return {"status": "ok"}

# =====================================================
# VERIFY
# =====================================================
@app.get("/verify-payment")
def verify_payment(session_id: str):

    return {"paid": session_id in paid_sessions}

# =====================================================
# PDF (UNCHANGED BUT SAFE)
# =====================================================
@app.get("/download-pdf")
def download_pdf(query: str, session_id: str = None):

    if session_id not in paid_sessions:
        return {"error": "Payment required"}

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 60

    GREEN = HexColor("#22c55e")
    ORANGE = HexColor("#f59e0b")
    RED = HexColor("#ef4444")
    DARK = HexColor("#111827")

    novelty = 72
    risk = "Medium"

    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, y, "PatentHound Report")

    y -= 40

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Query: {query}")

    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"Novelty Score: {novelty}/100")

    y -= 20
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Risk Level: {risk}")

    y -= 40

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Similar Patents")

    y -= 20

    for i in range(3):
        p.setFont("Helvetica", 10)
        p.drawString(50, y, f"- {query} related patent example {i+1}")
        y -= 15

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"}
    )
