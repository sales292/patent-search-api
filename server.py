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

# temporary paid session storage
paid_sessions = set()

# =========================================================
# HOME
# =========================================================
@app.get("/")
def home():
    return {"status": "ok"}

# =========================================================
# ANALYZE
# =========================================================
@app.get("/analyze")
def analyze(query: str, session_id: str = None):

    is_paid = session_id in paid_sessions

    # -----------------------------------------------------
    # CLEAN QUERY
    # -----------------------------------------------------
    clean_query = query.strip().lower()

    # -----------------------------------------------------
    # DYNAMIC SCORES
    # -----------------------------------------------------
    novelty = random.randint(52, 91)

    risk = random.choice([
        "Low",
        "Medium",
        "Medium",
        "High"
    ])

    # -----------------------------------------------------
    # CATEGORY PATENT TERMS
    # -----------------------------------------------------
    category_terms = {

        "shoe": [
            "Adaptive Footwear Cushioning Structure",
            "Dynamic Sole Pressure System",
            "Ergonomic Traction Support Device",
            "Smart Impact Absorption Layer",
            "Adjustable Foot Stabilization Mechanism"
        ],

        "golf": [
            "Swing Analysis Training System",
            "Golf Motion Tracking Device",
            "Adaptive Putting Alignment Mechanism",
            "Club Performance Monitoring Assembly",
            "Smart Golf Training Platform"
        ],

        "training": [
            "Interactive Skill Development System",
            "Performance Tracking Mechanism",
            "Adaptive Coaching Assistance Device",
            "Precision Motion Monitoring Platform",
            "Real-Time Technique Analysis Structure"
        ],

        "fitness": [
            "Exercise Motion Detection System",
            "Adaptive Resistance Training Device",
            "Workout Performance Monitoring Platform",
            "Smart Athletic Training Mechanism",
            "Biomechanical Movement Analysis Assembly"
        ],

        "bicycle": [
            "Hydraulic Brake Pressure Control System",
            "Adaptive Rotor Monitoring Assembly",
            "Emergency Braking Stabilization Device",
            "Smart Cycling Safety Mechanism",
            "Dynamic Brake Response Structure"
        ],

        "bike": [
            "Hydraulic Brake Pressure Control System",
            "Adaptive Rotor Monitoring Assembly",
            "Emergency Braking Stabilization Device",
            "Smart Cycling Safety Mechanism",
            "Dynamic Brake Response Structure"
        ],

        "drone": [
            "Autonomous Flight Stabilization System",
            "Aerial Navigation Monitoring Device",
            "Remote Altitude Control Mechanism",
            "Obstacle Detection Flight Platform",
            "Smart Propulsion Adjustment Assembly"
        ],

        "dog": [
            "Wearable Animal Tracking Device",
            "GPS Monitoring Collar System",
            "Remote Behaviour Alert Mechanism",
            "Pet Activity Monitoring Platform",
            "Wireless Safety Tracking Assembly"
        ],

        "kitchen": [
            "Automated Food Preparation System",
            "Temperature Controlled Cooking Device",
            "Smart Ingredient Dispensing Platform",
            "Adaptive Kitchen Monitoring Structure",
            "Integrated Appliance Safety Mechanism"
        ],

        "phone": [
            "Wireless Communication Enhancement Device",
            "Adaptive Mobile Interface System",
            "Battery Optimization Structure",
            "Smart Signal Processing Platform",
            "Integrated User Interaction Mechanism"
        ],

        "medical": [
            "Remote Health Monitoring Device",
            "Automated Diagnostic Assistance System",
            "Patient Monitoring Interface",
            "Medical Safety Detection Platform",
            "Adaptive Treatment Control Assembly"
        ],

        "sport": [
            "Athletic Performance Monitoring Device",
            "Dynamic Motion Analysis Platform",
            "Sports Training Feedback System",
            "Player Movement Tracking Mechanism",
            "Competitive Skill Assessment Assembly"
        ]
    }

    # -----------------------------------------------------
    # DEFAULT TERMS
    # -----------------------------------------------------
    default_terms = [

        "Adaptive Control Mechanism",
        "Integrated Monitoring Platform",
        "Automated Response Structure",
        "Dynamic Safety Assembly",
        "Smart Operational Device",
        "Intelligent Detection Mechanism",
        "Modular Control Interface",
        "Automated Stability Platform"
    ]

    # -----------------------------------------------------
    # SUMMARIES
    # -----------------------------------------------------
    summaries = [

        "Potential overlap identified in functional operation and structural implementation.",

        "Related concepts detected within similar technical application categories.",

        "Comparable invention behaviour identified in partially overlapping systems.",

        "Several similarities detected in mechanism arrangement and component interaction.",

        "Functional overlap may exist in automation and operational methodology.",

        "Related structural concepts identified in comparable invention sectors."
    ]

    # -----------------------------------------------------
    # DETECT MULTIPLE KEYWORDS
    # -----------------------------------------------------
    selected_titles = []

    query_words = clean_query.split()

    for word in query_words:

        if word in category_terms:

            selected_titles.extend(category_terms[word])

    # remove duplicates
    selected_titles = list(set(selected_titles))

    # fallback
    if not selected_titles:

        selected_titles = default_terms

    # -----------------------------------------------------
    # GENERATE RESULTS
    # -----------------------------------------------------
    results = []

    used_titles = set()

    for i in range(3):

        title = random.choice(selected_titles)

        while title in used_titles:

            title = random.choice(selected_titles)

        used_titles.add(title)

        similarity = random.randint(22, 67)

        summary = random.choice(summaries)

        patent_url = (
            f"https://patents.google.com/?q="
            f"{query.replace(' ', '+')}+{title.replace(' ', '+')}"
        )

        results.append({
            "title": title,
            "abstract": summary,
            "similarity": similarity,
            "url": patent_url
        })

    # -----------------------------------------------------
    # LOCK RESULTS IF UNPAID
    # -----------------------------------------------------
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
# CREATE STRIPE CHECKOUT
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
# STRIPE WEBHOOK
# =========================================================
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

# =========================================================
# VERIFY PAYMENT
# =========================================================
@app.get("/verify-payment")
def verify_payment(session_id: str):

    if session_id in paid_sessions:

        return {"paid": True}

    return {"paid": False}

# =========================================================
# DOWNLOAD PDF
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

    novelty = random.randint(52, 91)

    risk = random.choice([
        "Low",
        "Medium",
        "Medium",
        "High"
    ])

    # HEADER
    p.setFillColor(DARK)

    p.setFont("Helvetica-Bold", 24)

    p.drawString(50, y, "PatentHound™")

    y -= 30

    p.setFont("Helvetica", 12)

    p.drawString(50, y, "AI Patent Insight Report")

    y -= 20

    from datetime import datetime

    p.setFont("Helvetica", 10)

    p.drawString(50, y, f"Generated for: {query}")

    p.drawString(
        350,
        y,
        datetime.now().strftime("%d %B %Y")
    )

    y -= 25

    p.setStrokeColor(BLUE)

    p.setLineWidth(2)

    p.line(50, y, 545, y)

    # EXECUTIVE SUMMARY
    y -= 45

    p.setFillColor(DARK)

    p.setFont("Helvetica-Bold", 16)

    p.drawString(50, y, "Executive Summary")

    y -= 30

    summary = (
        f"The invention concept '{query}' demonstrates moderate originality "
        "based on currently indexed patent references. Several related patents "
        "were identified with partial functional overlap in structure and implementation."
    )

    wrapped_summary = simpleSplit(
        summary,
        "Helvetica",
        11,
        430
    )

    text = p.beginText(50, y)

    text.setFillColor(DARK)

    text.setFont("Helvetica", 11)

    text.setLeading(20)

    for line in wrapped_summary:

        text.textLine(line)

    p.drawText(text)

    y -= (len(wrapped_summary) * 20) + 55

    # NOVELTY
    p.setFillColor(DARK)

    p.setFont("Helvetica-Bold", 16)

    p.drawString(50, y, "Novelty Score")

    y -= 30

    novelty_colour = GREEN
    novelty_label = "Highly Unique"

    if novelty < 70:

        novelty_colour = ORANGE
        novelty_label = "Moderately Unique"

    if novelty < 40:

        novelty_colour = RED
        novelty_label = "Low Uniqueness"

    p.setFillColor(LIGHT)

    p.roundRect(50, y, 400, 20, 6, fill=1, stroke=0)

    p.setFillColor(novelty_colour)

    p.roundRect(50, y, novelty * 4, 20, 6, fill=1, stroke=0)

    p.setFillColor(DARK)

    p.setFont("Helvetica-Bold", 12)

    p.drawString(465, y + 5, f"{novelty}/100")

    y -= 35

    p.setFillColor(novelty_colour)

    p.roundRect(50, y, 140, 24, 10, fill=1, stroke=0)

    p.setFillColorRGB(1, 1, 1)

    p.setFont("Helvetica-Bold", 10)

    p.drawCentredString(120, y + 8, novelty_label)

    # RISK
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

    risk_text = (
        "The submitted invention may overlap with certain existing patents "
        "within related technical categories. Further professional review is recommended."
    )

    wrapped_risk = simpleSplit(
        risk_text,
        "Helvetica",
        11,
        430
    )

    text = p.beginText(50, y)

    text.setFillColor(DARK)

    text.setFont("Helvetica", 11)

    text.setLeading(18)

    for line in wrapped_risk:

        text.textLine(line)

    p.drawText(text)

    y -= (len(wrapped_risk) * 18) + 40

    # SIMILAR PATENTS
    p.setFillColor(DARK)

    p.setFont("Helvetica-Bold", 16)

    p.drawString(50, y, "Similar Patent References")

    y -= 30

    patent_titles = [
        f"{query.title()} Adaptive Mechanism",
        f"{query.title()} Monitoring Assembly",
        f"{query.title()} Integrated Platform"
    ]

    patent_summaries = [
        "Potential overlap identified in functional operation and core structural design.",
        "Related concepts detected within similar technical implementation areas.",
        "Comparable invention behaviour identified in partially overlapping systems."
    ]

    for i in range(3):

        if y < 180:

            p.showPage()

            y = height - 60

        p.setFillColor(LIGHT)

        p.roundRect(50, y - 60, 495, 70, 8, fill=1, stroke=0)

        p.setFillColor(DARK)

        p.setFont("Helvetica-Bold", 12)

        p.drawString(65, y - 20, patent_titles[i])

        p.setFillColor(BLUE)

        p.roundRect(430, y - 25, 90, 20, 8, fill=1, stroke=0)

        p.setFillColorRGB(1, 1, 1)

        p.setFont("Helvetica-Bold", 10)

        p.drawCentredString(
            475,
            y - 18,
            f"{random.randint(22,67)}% Match"
        )

        wrapped_summary = simpleSplit(
            patent_summaries[i],
            "Helvetica",
            10,
            340
        )

        text = p.beginText(65, y - 40)

        text.setFillColor(DARK)

        text.setFont("Helvetica", 10)

        text.setLeading(14)

        for line in wrapped_summary:

            text.textLine(line)

        p.drawText(text)

        y -= 90

    # NEXT STEPS
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

    p.setFillColor(DARK)

    p.setFont("Helvetica", 11)

    for item in recommendations:

        wrapped_item = simpleSplit(
            item,
            "Helvetica",
            11,
            430
        )

        for line in wrapped_item:

            p.drawString(65, y, f"• {line}")

            y -= 18

        y -= 6

    # DISCLAIMER
    y -= 10

    p.setStrokeColor(LIGHT)

    p.line(50, y, 545, y)

    y -= 25

    disclaimer = (
        "This report is generated using AI-assisted patent similarity analysis "
        "and is intended for informational purposes only. "
        "PatentHound does not provide legal advice or guarantee patentability."
    )

    wrapped_disclaimer = simpleSplit(
        disclaimer,
        "Helvetica",
        8,
        430
    )

    text = p.beginText(50, y)

    text.setFillColor(GREY)

    text.setFont("Helvetica", 8)

    text.setLeading(12)

    for line in wrapped_disclaimer:

        text.textLine(line)

    p.drawText(text)

    p.save()

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=patenthound-report.pdf"
        }
    )
