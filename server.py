from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import os
import stripe
import json
import requests
import hashlib
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

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
    return {"status": "PatentHound SaaS Online"}

# =========================================================
# ---------------- INTELLIGENCE CORE ----------------
# =========================================================

DOMAIN_MAP = {
    "phone": ["mobile device", "smartphone", "electronics"],
    "water": ["bottle", "hydration", "container"],
    "hold": ["mount", "attachment", "fixture"],
    "bike": ["bicycle", "cycling", "transport"],
    "golf": ["sports", "training", "swing mechanics"],
    "shoe": ["footwear", "support system"],
    "device": ["system", "apparatus", "mechanism"],
    "wearable": ["sensor", "tracking device"]
}

FUNCTIONAL_TERMS = {
    "mount", "hold", "attach", "support", "control",
    "detect", "monitor", "track", "system", "device", "mechanism"
}

# =========================================================
# QUERY NORMALISATION (KEY TO CONSISTENCY)
# =========================================================
def normalise_query(query: str):

    q = query.lower().split()
    expanded = set(q)

    for w in q:
        if w in DOMAIN_MAP:
            expanded.update(DOMAIN_MAP[w])

    return sorted(list(expanded))


# =========================================================
# REAL PATENT DATA FETCH
# =========================================================
def fetch_patents(query: str):

    url = f"https://patents.google.com/?q={quote_plus(query)}"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        results = []

        items = soup.select("search-result-item, article, div")

        for item in items[:10]:

            h = item.find("h3")
            if not h:
                continue

            title = h.get_text(strip=True)

            a = item.find("a", href=True)
            link = a["href"] if a else url

            if link.startswith("/"):
                link = "https://patents.google.com" + link

            span = item.find("span")
            snippet = span.get_text(strip=True) if span else ""

            results.append({
                "title": title,
                "abstract": snippet or "Patent record from Google Patents.",
                "url": link
            })

        if not results:
            results = [{
                "title": "Google Patents Search Results",
                "abstract": "No structured results parsed — fallback to search link.",
                "url": url
            }]

        return results

    except Exception:
        return [{
            "title": "Patent search unavailable",
            "abstract": "Fallback search link provided.",
            "url": url
        }]

# =========================================================
# INFRINGEMENT INTELLIGENCE ENGINE
# =========================================================
def calculate_risk(query, title, abstract):

    q_tokens = set(query.lower().split())
    t_tokens = set(title.lower().split())
    a_tokens = set(abstract.lower().split())

    overlap = len(q_tokens & t_tokens) * 3 + len(q_tokens & a_tokens) * 2
    functional_overlap = len(q_tokens & FUNCTIONAL_TERMS) * 2

    score = overlap + functional_overlap

    # normalize to 0–100
    return min(100, score * 6)


# =========================================================
# AI LEGAL ANALYST LAYER (INVESTOR FEATURE)
# =========================================================
def analyst_reasoning(query, title, abstract, score):

    q = set(query.lower().split())
    t = set(title.lower().split())

    overlaps = list(q & t)

    if score >= 70:
        risk = "HIGH infringement exposure"
        insight = "strong structural + functional similarity detected"
    elif score >= 40:
        risk = "MEDIUM infringement exposure"
        insight = "partial overlap in functional implementation"
    else:
        risk = "LOW infringement exposure"
        insight = "limited prior art similarity detected"

    return {
        "risk_statement": risk,
        "analysis": insight,
        "matched_terms": overlaps[:6]
    }


# =========================================================
# ANALYZE ENDPOINT (INVESTOR-GRADE OUTPUT)
# =========================================================
@app.get("/analyze")
def analyze(query: str, session_id: str = None):

    is_paid = session_id in paid_sessions

    normalised = " ".join(normalise_query(query))

    patents = fetch_patents(normalised)

    analysed = []

    for p in patents:

        score = calculate_risk(query, p["title"], p["abstract"])
        reasoning = analyst_reasoning(query, p["title"], p["abstract"], score)

        analysed.append({
            "title": p["title"],
            "abstract": p["abstract"][:260],
            "similarity": score,
            "reasoning": reasoning,
            "url": p["url"]
        })

    analysed.sort(key=lambda x: x["similarity"], reverse=True)

    top = analysed[:5]

    avg = sum(x["similarity"] for x in top) / len(top)

    if avg >= 70:
        risk_level = "High"
    elif avg >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    novelty = max(10, 100 - int(avg))

    # LOCK (UNCHANGED FRONTEND CONTRACT)
    if not is_paid:
        top = [
            {
                "title": x["title"],
                "abstract": "🔒 Unlock full report",
                "similarity": None,
                "reasoning": None,
                "url": None
            }
            for x in top
        ]

    return {
        "query": query,
        "novelty": novelty,
        "risk": risk_level,
        "paid": is_paid,
        "results": top
    }


# =========================================================
# STRIPE
# =========================================================
@app.post("/create-checkout")
def create_checkout():

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": "PatentHound Pro Report"},
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
# PDF (CLEAN INVESTOR REPORT)
# =========================================================
@app.get("/download-pdf")
def download_pdf(query: str, session_id: str = None):

    if session_id not in paid_sessions:
        return {"error": "Payment required"}

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    y = 800

    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, y, "PatentHound Investor Intelligence Report")

    y -= 40

    summary = f"The invention '{query}' was analysed using AI infringement intelligence + real patent dataset retrieval."

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
        headers={"Content-Disposition": "attachment; filename=patenthound-investor-report.pdf"}
    )
