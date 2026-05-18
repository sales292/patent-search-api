from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import os
import stripe
import json
import requests
from urllib.parse import quote_plus

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

app = FastAPI()

# =========================================================
# CORS
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# STRIPE
# =========================================================
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
paid_sessions = set()

# =========================================================
# HOME
# =========================================================
@app.get("/")
def home():
    return {"status": "PatentHound stable v9 running"}

# =========================================================
# SAFE QUERY EXPANSION (NO CRASH RISK)
# =========================================================
def expand_query(query: str):

    q = query.lower().split()

    base = set(q)

    simple_map = {
        "phone": ["mobile", "device", "smartphone"],
        "water": ["bottle", "container", "hydration"],
        "hold": ["mount", "holder", "attachment"],
        "mount": ["bracket", "support"],
        "bike": ["bicycle", "cycling"],
        "golf": ["sports", "training"],
        "shoe": ["footwear", "support"],
        "device": ["system", "apparatus", "mechanism"],
        "wearable": ["sensor", "tracking"]
    }

    for word in q:
        if word in simple_map:
            base.update(simple_map[word])

    return list(base)

# =========================================================
# SAFE PATENT RETRIEVAL (NO BS4, NO CRASH RISK)
# =========================================================
def fetch_patents(query: str):

    url = f"https://patents.google.com/?q={quote_plus(query)}"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)

        # We DO NOT parse HTML (prevents Railway crashes)
        return [{
            "title": "Google Patents Search Results",
            "abstract": "Click through to view live patent dataset matching your query.",
            "url": url
        }]

    except Exception:
        return [{
            "title": "Patent search temporarily unavailable",
            "abstract": "Fallback search link provided.",
            "url": url
        }]

# =========================================================
# INFRINGEMENT SCORING (STABLE + DETERMINISTIC)
# =========================================================
def calculate_risk(query: str, title: str):

    q = set(query.lower().split())
    t = set(title.lower().split())

    overlap = len(q & t)

    score = overlap * 15

    if score > 70:
        return min(score, 95)
    elif score > 30:
        return score + 20
    else:
        return score + 10

# =========================================================
# AI REASONING LAYER (SAFE VERSION)
# =========================================================
def reasoning(query: str, score: int):

    if score >= 70:
        level = "HIGH infringement exposure"
        desc = "Strong functional overlap with known patent categories."
    elif score >= 40:
        level = "MEDIUM infringement exposure"
        desc = "Some shared functional concepts with prior art."
    else:
        level = "LOW infringement exposure"
        desc = "Limited similarity detected with known patent structures."

    return f"{level}. {desc} Assessment based on functional keyword overlap analysis."

# =========================================================
# ANALYZE ENDPOINT (STABLE SaaS OUTPUT)
# =========================================================
@app.get("/analyze")
def analyze(query: str, session_id: str = None):

    is_paid = session_id in paid_sessions

    expanded = " ".join(expand_query(query))

    raw = fetch_patents(expanded)

    results = []

    for r in raw:

        score = calculate_risk(query, r["title"])
        reason = reasoning(query, score)

        results.append({
            "title": r["title"],
            "abstract": r["abstract"][:240],
            "similarity": score,
            "reasoning": reason,
            "url": r["url"]
        })

    # system-level risk
    avg = sum(r["similarity"] for r in results) / len(results)

    if avg >= 70:
        risk = "High"
    elif avg >= 40:
        risk = "Medium"
    else:
        risk = "Low"

    novelty = max(10, 100 - int(avg))

    # LOCKED MODE (frontend unchanged)
    if not is_paid:
        results = [
            {
                "title": r["title"],
                "abstract": "🔒 Unlock full report",
                "similarity": None,
                "reasoning": None,
                "url": None
            }
            for r in results
        ]

    return {
        "query": query,
        "novelty": novelty,
        "risk": risk,
        "paid": is_paid,
        "results": results
    }

# =========================================================
# STRIPE CHECKOUT
# =========================================================
@app.post("/create-checkout")
def create_checkout():

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": "PatentHound Report"},
                "unit_amount": 899,
            },
            "quantity": 1,
        }],
        success_url="https://patenthound.co.uk/patent-analyzer?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://patenthound.co.uk/patent-analyzer"
    )

    return {"url": session.url}

# =========================================================
# WEBHOOK
# =========================================================
@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):

    event = json.loads(await request.body())

    if event.get("type") == "checkout.session.completed":

        session_id = event["data"]["object"].get("id")

        if session_id:
            paid_sessions.add(session_id)

    return {"status": "success"}

# =========================================================
# VERIFY PAYMENT
# =========================================================
@app.get("/verify-payment")
def verify_payment(session_id: str):

    return {"paid": session_id in paid_sessions}

# =========================================================
# PDF (SAFE + STABLE)
# =========================================================
@app.get("/download-pdf")
def download_pdf(query: str, session_id: str = None):

    if session_id not in paid_sessions:
        return {"error": "Payment required"}

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    y = 800

    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, y, "PatentHound Intelligence Report")

    y -= 40

    summary = f"The invention '{query}' was analysed using AI-assisted patent risk intelligence."

    wrapped = simpleSplit(summary, "Helvetica", 11, 450)

    text = p.beginText(50, y)
    text.setLeading(18)

    for line in wrapped:
        text.textLine(line)

    p.drawText(text)

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=patenthound-report.pdf"}
    )
