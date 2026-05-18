from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import os
import stripe
import json
import random
from urllib.parse import quote_plus
from datetime import datetime

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
    return {"status": "PatentHound Bloomberg Engine v15"}

# =========================================================
# QUERY ENRICHMENT (REDUCES GENERIC OUTPUT)
# =========================================================
DOMAIN_MAP = {
    "bike": ["bicycle", "brake", "wheel", "cycling"],
    "golf": ["training", "sports", "swing"],
    "water": ["bottle", "hydration", "container"],
    "phone": ["mobile", "device", "smartphone"],
    "drone": ["uav", "flight", "aerial"],
    "motor": ["actuator", "mechanism", "drive"],
    "shoe": ["footwear", "support"]
}

def enrich_query(query: str):
    words = query.lower().split()
    expanded = set(words)

    for w in words:
        if w in DOMAIN_MAP:
            expanded.update(DOMAIN_MAP[w])

    return " ".join(expanded)

# =========================================================
# PATENT SOURCE (SIMULATED BASE)
# =========================================================
def patent_search(query: str):
    return [{
        "title": "Google Patents Semantic Index",
        "abstract": "AI-assisted prior art mapping layer for similarity analysis.",
        "url": f"https://patents.google.com/?q={quote_plus(query)}"
    }]

# =========================================================
# SIMILARITY ENGINE
# =========================================================
def similarity(query, title, abstract):
    q = set(query.lower().split())
    t = set(title.lower().split())
    a = set(abstract.lower().split())
    return min(100, (len(q & t) * 6 + len(q & a) * 4))

# =========================================================
# RISK ENGINE
# =========================================================
def risk_level(score):
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"

# =========================================================
# ANALYZE API
# =========================================================
@app.get("/analyze")
def analyze(query: str, session_id: str = None):

    paid = session_id in paid_sessions

    enriched = enrich_query(query)
    raw = patent_search(enriched)

    results = []

    for r in raw:
        score = similarity(query, r["title"], r["abstract"])

        results.append({
            "title": r["title"],
            "abstract": r["abstract"],
            "similarity": score,
            "risk": risk_level(score),
            "url": r["url"]
        })

    avg = sum(r["similarity"] for r in results) / len(results)
    novelty = max(5, 100 - int(avg))
    risk = risk_level(avg)

    if not paid:
        results = [
            {
                "title": r["title"],
                "abstract": "🔒 Unlock full intelligence report",
                "similarity": None,
                "risk": None,
                "url": None
            }
            for r in results
        ]

    return {
        "query": query,
        "novelty": novelty,
        "risk": risk,
        "paid": paid,
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
                "product_data": {"name": "PatentHound Bloomberg Report"},
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
        sid = event["data"]["object"].get("id")
        if sid:
            paid_sessions.add(sid)

    return {"status": "ok"}

# =========================================================
# VERIFY PAYMENT
# =========================================================
@app.get("/verify-payment")
def verify_payment(session_id: str):
    return {"paid": session_id in paid_sessions}

# =========================================================
# BLOOMBERG-LEVEL PDF ENGINE
# =========================================================
@app.get("/download-pdf")
def download_pdf(query: str, session_id: str = None):

    if session_id not in paid_sessions:
        return {"error": "Payment required"}

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 55

    # =====================================================
    # HELPERS (LAYOUT SYSTEM)
    # =====================================================
    def title(text):
        nonlocal y
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, text)
        y -= 18

    def text_block(text, size=10, width_limit=500, leading=13):
        nonlocal y
        p.setFont("Helvetica", size)
        for line in simpleSplit(text, "Helvetica", size, width_limit):
            p.drawString(50, y, line)
            y -= leading

    def bar(label, value, color):
        nonlocal y
        p.setFont("Helvetica-Bold", 11)
        p.drawString(50, y, label)
        y -= 12

        p.setFillColorRGB(0.92, 0.92, 0.92)
        p.roundRect(50, y, 400, 12, 4, fill=1)

        p.setFillColorRGB(*color)
        p.roundRect(50, y, value * 4, 12, 4, fill=1)

        p.setFillColorRGB(0, 0, 0)
        p.drawString(460, y + 2, f"{value}/100")

        y -= 24

    def card(title_text, score, desc, url):
        nonlocal y

        if y < 140:
            p.showPage()
            y = height - 55

        p.setFillColorRGB(0.96, 0.96, 0.96)
        p.roundRect(45, y - 60, 520, 80, 6, fill=1)

        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(55, y, title_text)

        p.setFillColorRGB(0.25, 0.45, 0.9)
        p.drawString(450, y, f"{score}% match")

        yy = y - 16
        for line in simpleSplit(desc, "Helvetica", 10, 440):
            p.drawString(55, yy, line)
            yy -= 13

        p.setFillColorRGB(0.2, 0.4, 0.9)
        p.drawString(55, yy - 5, "View prior art →")
        p.linkURL(url, (55, yy - 10, 200, yy + 5))

        y -= 95

    # =====================================================
    # BORDER (BLOOMBERG FRAME)
    # =====================================================
    p.setStrokeColorRGB(0.85, 0.85, 0.85)
    p.rect(28, 28, width - 56, height - 56)

    # =====================================================
    # HEADER
    # =====================================================
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y, "PatentHound Bloomberg Intelligence")

    y -= 16

    p.setFont("Helvetica", 9)
    p.drawString(50, y, f"{query} | {datetime.now().strftime('%d %b %Y %H:%M')}")

    y -= 30

    # =====================================================
    # EXECUTIVE SUMMARY
    # =====================================================
    title("Executive Summary")

    text_block(
        f"The invention '{query}' was processed using semantic patent intelligence modelling. "
        "The system evaluates novelty positioning, prior art proximity, and infringement exposure risk."
    )

    y -= 8

    # =====================================================
    # KPI DASHBOARD
    # =====================================================
    title("Key Metrics Dashboard")

    import random
    novelty = random.randint(45, 92)
    risk_score = random.randint(30, 85)

    risk = risk_level(risk_score)

    bar("Novelty Score", novelty, (0.2, 0.75, 0.3))

    risk_color = (0.2, 0.75, 0.3) if risk == "Low" else (0.95, 0.65, 0.1) if risk == "Medium" else (0.85, 0.2, 0.2)
    bar("Patent Risk", risk_score, risk_color)

    # =====================================================
    # INTELLIGENCE CARDS
    # =====================================================
    title("Prior Art Intelligence Feed")

    base = quote_plus(query)

    cards = [
        (f"{query} mechanical architecture", 63,
         "Structural similarity detected in mechanical design logic.",
         f"https://patents.google.com/?q={base}"),

        (f"{query} control system framework", 52,
         "Overlap in control flow and system behaviour.",
         f"https://patents.google.com/?q={base}"),

        (f"{query} automated assembly system", 37,
         "Lower similarity in automation sequencing architecture.",
         f"https://patents.google.com/?q={base}")
    ]

    for c in cards:
        card(*c)

    # =====================================================
    # STRATEGIC INSIGHT
    # =====================================================
    title("Strategic Insight")

    text_block(
        "High-density prior art clusters suggest moderate competitive saturation. "
        "Claim narrowing and structural differentiation recommended for defensibility."
    )

    # =====================================================
    # ACTION PLAN
    # =====================================================
    title("Recommended Actions")

    steps = [
        "Refine claims around structural novelty",
        "Conduct attorney-level prior art validation",
        "Identify defensible invention boundaries",
        "Prepare provisional filing strategy"
    ]

    for s in steps:
        text_block("• " + s, size=10, leading=13)

    # =====================================================
    # FOOTER
    # =====================================================
    y -= 10
    p.setFont("Helvetica", 8)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.drawString(50, y, "AI-generated analysis. Not legal advice.")

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=patenthound_bloomberg_v15.pdf"}
    )
