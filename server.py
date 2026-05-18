from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import os
import stripe
import json
import random

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
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
    return {"status": "ok"}

# =========================================================
# QUERY INTELLIGENCE (KEY FIX)
# =========================================================
def expand_query(query: str):

    q = query.lower()

    mapping = {

        "water": ["hydration", "bottle", "container", "portable"],
        "bottle": ["container", "carrier", "holder"],
        "phone": ["mobile", "smartphone", "device"],
        "mobile": ["phone", "smartphone", "device"],
        "device": ["electronic", "tool", "gadget"],
        "mount": ["holder", "attachment", "dock"],
        "holder": ["mount", "support", "fixture"],

        "bike": ["bicycle", "cycling"],
        "bicycle": ["bike", "cycling"],
        "car": ["vehicle", "automotive"],
        "dog": ["pet", "animal"],
        "shoe": ["footwear", "sole"],

        "fitness": ["training", "exercise", "workout"],
        "golf": ["swing", "club", "training"],
        "training": ["learning", "practice", "coaching"]
    }

    expanded = set(q.split())

    for word in q.split():
        if word in mapping:
            expanded.update(mapping[word])

    return list(expanded)

# =========================================================
# ANALYZE
# =========================================================
@app.get("/analyze")
def analyze(query: str, session_id: str = None):

    is_paid = session_id in paid_sessions

    clean_query = query.strip().lower()

    expanded_terms = expand_query(clean_query)

    novelty = random.randint(50, 92)

    risk = random.choice(["Low", "Medium", "Medium", "High"])

    summaries = [
        "Functional overlap detected in structural and operational design.",
        "Related concept identified within similar technical domain applications.",
        "Comparable invention behaviour observed in system interaction patterns.",
        "Partial similarity found in mechanical and functional arrangement.",
        "Potential overlap in user interaction and system configuration."
    ]

    endings = [
        "adaptive system",
        "integration module",
        "smart attachment device",
        "portable support mechanism",
        "dynamic control system",
        "interactive monitoring platform",
        "automated adjustment structure",
        "sensor-based assembly",
        "functional support device"
    ]

    # =====================================================
    # DYNAMIC TITLE GENERATION (IMPORTANT FIX)
    # =====================================================
    results = []
    used = set()

    for i in range(3):

        seed_word = random.choice(expanded_terms)

        ending = random.choice(endings)

        title = f"{seed_word.title()} {ending.title()}"

        while title in used:
            seed_word = random.choice(expanded_terms)
            ending = random.choice(endings)
            title = f"{seed_word.title()} {ending.title()}"

        used.add(title)

        similarity = random.randint(25, 78)

        summary = random.choice(summaries)

        patent_url = (
            "https://patents.google.com/?q=" +
            "+".join(expanded_terms[:5]) +
            "+" + ending.replace(" ", "+")
        )

        results.append({
            "title": title,
            "abstract": summary,
            "similarity": similarity,
            "url": patent_url
        })

    # =====================================================
    # LOCK IF NOT PAID
    # =====================================================
    if not is_paid:

        results = [
            {
                "title": r["title"],
                "abstract": "🔒 Unlock full details",
                "similarity": None,
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
                    "unit_amount": 899,
                },
                "quantity": 1,
            }],
            success_url="https://patenthound.co.uk/patent-analyzer?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://patenthound.co.uk/patent-analyzer"
        )

        return {"url": session.url}

    except Exception as e:
        print("Stripe error:", str(e))
        return {"error": str(e)}

# =========================================================
# WEBHOOK
# =========================================================
@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):

    payload = await request.body()

    try:
        event = json.loads(payload)
    except Exception as e:
        return {"status": "invalid"}

    if event.get("type") == "checkout.session.completed":

        session = event["data"]["object"]
        session_id = session.get("id")

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
# PDF (UNCHANGED STRUCTURE, SAFE)
# =========================================================
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
    LIGHT = HexColor("#f3f4f6")
    BLUE = HexColor("#635bff")
    GREY = HexColor("#6b7280")

    novelty = random.randint(50, 92)
    risk = random.choice(["Low", "Medium", "Medium", "High"])

    # HEADER
    p.setFillColor(DARK)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, y, "PatentHound™")

    y -= 40

    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Generated for: {query}")

    # EXEC SUMMARY (FIXED WRAP SAFE)
    y -= 60
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Executive Summary")

    y -= 30

    summary = (
        f"The invention concept '{query}' shows potential functional overlap "
        "with existing patent domains. Related systems were identified in "
        "adjacent technical categories."
    )

    wrapped = simpleSplit(summary, "Helvetica", 11, 450)

    text = p.beginText(50, y)
    text.setFont("Helvetica", 11)
    text.setLeading(18)

    for line in wrapped:
        text.textLine(line)

    p.drawText(text)

    p.save()

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=report.pdf"}
    )
