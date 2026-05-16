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
from reportlab.lib.utils import simpleSplit

app = FastAPI()

# -----------------------
# CORS
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock to your domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# STRIPE SETUP
# -----------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# store paid sessions (MVP - upgrade to DB later)
paid_sessions = set()

# -----------------------
# HEALTH CHECK
# -----------------------
@app.get("/")
def home():
    return {"status": "ok"}

# -----------------------
# ANALYZE ENDPOINT
# -----------------------
@app.get("/analyze")
def analyze(query: str, session_id: str = None):

    is_paid = session_id in paid_sessions

    results = [
        {"title": f"{query} system A", "abstract": "Patent example A", "similarity": 42},
        {"title": f"{query} system B", "abstract": "Patent example B", "similarity": 31},
        {"title": f"{query} system C", "abstract": "Patent example C", "similarity": 18},
    ]

    if not is_paid:
        results = [
            {
                "title": r["title"],
                "abstract": "🔒 Unlock full details",
                "similarity": None
            }
            for r in results
        ]

    return {
        "query": query,
        "novelty": 70,
        "risk": "Medium",
        "paid": is_paid,
        "results": results
    }

# -----------------------
# STRIPE CHECKOUT
# -----------------------
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

# -----------------------
# STRIPE WEBHOOK (SOURCE OF TRUTH)
# -----------------------
@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):

    payload = await request.body()

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

# -----------------------
# VERIFY PAYMENT (FRONTEND SAFE CHECK)
# -----------------------
@app.get("/verify-payment")
def verify_payment(session_id: str):

    if session_id in paid_sessions:
        return {"paid": True}

    return {"paid": False}

# -----------------------
# PDF DOWNLOAD (PROTECTED)
# -----------------------
@app.get("/download-pdf")
def download_pdf(query: str, session_id: str = None):

    # verify payment
    if session_id not in paid_sessions:
        return {"error": "Payment required"}

    buffer = BytesIO()

    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    y = height - 60

    # ==========================================
    # COLOURS
    # ==========================================
    GREEN = HexColor("#22c55e")
    ORANGE = HexColor("#f59e0b")
    RED = HexColor("#ef4444")
    DARK = HexColor("#111827")
    LIGHT = HexColor("#f3f4f6")
    BLUE = HexColor("#635bff")

    novelty = 72
    risk = "Medium"

    # ==========================================
    # HEADER
    # ==========================================
    p.setFillColor(DARK)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, y, "PatentHound™")

    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, "AI Patent Insight Report")

    y -= 20

    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Generated for: {query}")

    from datetime import datetime
    p.drawString(350, y, datetime.now().strftime("%d %B %Y"))

    y -= 25

    p.setStrokeColor(BLUE)
    p.setLineWidth(2)
    p.line(50, y, 545, y)

    # ==========================================
    # EXECUTIVE SUMMARY
    # ==========================================
    y -= 45

    p.setFillColor(DARK)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Executive Summary")

    y -= 25

    p.setFont("Helvetica", 11)

    summary = (
    f"The invention concept '{query}' demonstrates moderate originality "
    "based on currently indexed patent references. Several related patents "
    "were identified with partial functional overlap in structure and implementation."
)

wrapped = simpleSplit(summary, "Helvetica", 11, 470)

text = p.beginText(50, y)
text.setLeading(18)

for line in wrapped:
    text.textLine(line)

p.drawText(text)

y -= (len(wrapped) * 18)

    # ==========================================
    # NOVELTY SCORE SECTION
    # ==========================================
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Novelty Score")

    y -= 30

    # novelty colour
    novelty_colour = GREEN
    novelty_label = "Highly Unique"

    if novelty < 70:
        novelty_colour = ORANGE
        novelty_label = "Moderately Unique"

    if novelty < 40:
        novelty_colour = RED
        novelty_label = "Low Uniqueness"

    # background bar
    p.setFillColor(LIGHT)
    p.roundRect(50, y, 400, 20, 6, fill=1, stroke=0)

    # score bar
    p.setFillColor(novelty_colour)
    p.roundRect(50, y, novelty * 4, 20, 6, fill=1, stroke=0)

    p.setFillColor(DARK)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(465, y + 5, f"{novelty}/100")

    y -= 35

    p.setFillColor(novelty_colour)
    p.roundRect(50, y, 120, 24, 10, fill=1, stroke=0)

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(110, y + 8, novelty_label)

    # ==========================================
    # RISK SECTION
    # ==========================================
    y -= 55

    p.setFillColor(DARK)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Patent Risk")

    y -= 30

    risk_colour = ORANGE

    if risk == "Low":
        risk_colour = GREEN

    if risk == "High":
        risk_colour = RED

    p.setFillColor(risk_colour)
    p.roundRect(50, y, 120, 24, 10, fill=1, stroke=0)

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(110, y + 8, f"{risk} Risk")

    y -= 40

    p.setFillColor(DARK)
    p.setFont("Helvetica", 11)

    risk_text = (
        "The submitted invention may overlap with certain existing patents "
        "within related technical categories. Further professional review is recommended."
    )

    text = p.beginText(50, y)
    text.setLeading(18)

    for line in risk_text.split(". "):
        text.textLine(line.strip())

    p.drawText(text)

    y -= 85

    # ==========================================
    # SIMILAR PATENTS SECTION
    # ==========================================
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Similar Patent References")

    y -= 30

    patents = [
        {
            "title": f"{query} mechanical control system",
            "match": "42%",
            "summary": "Mechanical structure overlap in operational design and braking functionality."
        },
        {
            "title": f"{query} hydraulic actuator mechanism",
            "match": "34%",
            "summary": "Partial similarity in component interaction and force application methodology."
        },
        {
            "title": f"{query} automated safety assembly",
            "match": "27%",
            "summary": "Lower overlap detected in automation and control sequencing behaviour."
        }
    ]

    for patent in patents:

        if y < 180:
            p.showPage()
            y = height - 60

        # card background
        p.setFillColor(LIGHT)
        p.roundRect(50, y - 60, 495, 70, 8, fill=1, stroke=0)

        # title
        p.setFillColor(DARK)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(65, y - 20, patent["title"])

        # match badge
        p.setFillColor(BLUE)
        p.roundRect(430, y - 25, 90, 20, 8, fill=1, stroke=0)

        p.setFillColorRGB(1, 1, 1)
        p.setFont("Helvetica-Bold", 10)
        p.drawCentredString(475, y - 18, patent["match"] + " Match")

        # summary
        p.setFillColor(DARK)
        p.setFont("Helvetica", 10)

        text = p.beginText(65, y - 40)
        text.setLeading(15)
        text.textLine(patent["summary"])
        p.drawText(text)

        y -= 90

    # ==========================================
    # RECOMMENDATIONS
    # ==========================================
    p.setFillColor(DARK)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Recommended Next Steps")

    y -= 30

    recommendations = [
    "Conduct a deeper patent search using Google Patents or a registered patent attorney",
    "Review claim wording within similar existing patents",
    "Document invention improvements and unique variations",
    "Consider provisional patent protection before public disclosure"
]
    p.setFont("Helvetica", 11)

    for item in recommendations:
        p.drawString(65, y, f"• {item}")
        y -= 22

    # ==========================================
    # DISCLAIMER
    # ==========================================
    y -= 20

    p.setStrokeColor(LIGHT)
    p.line(50, y, 545, y)

    y -= 25

    p.setFont("Helvetica", 8)
    p.setFillColor(HexColor("#6b7280"))

    disclaimer = (
        "This report is generated using AI-assisted patent similarity analysis "
        "and is intended for informational purposes only. "
        "PatentHound does not provide legal advice or guarantee patentability."
    )

    text = p.beginText(50, y)
    text.setLeading(12)

    for line in disclaimer.split(". "):
        text.textLine(line.strip())

    p.drawText(text)

    # ==========================================
    # FINALISE PDF
    # ==========================================
    p.save()

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=patenthound-report.pdf"
        }
    )
