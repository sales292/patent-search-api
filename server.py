from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = FastAPI()

# ------------------ Enable CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your domain for production, e.g., ["https://patenthound.co.uk"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ Mock Analyze Endpoint ------------------
@app.get("/analyze")
def analyze_idea(query: str):
    """
    Returns mock patent results for any input query.
    """
    results = [
        {
            "title": f"{query.title()} Self-Adjusting Device",
            "patent_number": "US1234567A",
            "abstract": f"A mechanism related to {query} that automatically adjusts for optimal performance.",
            "similarity": 25,
            "url": "https://patents.google.com/patent/US1234567A"
        },
        {
            "title": f"Automatic {query.title()} System",
            "patent_number": "US7654321B",
            "abstract": f"A system designed for {query} to activate automatically under certain conditions.",
            "similarity": 30,
            "url": "https://patents.google.com/patent/US7654321B"
        },
        {
            "title": f"Hydraulic {query.title()} Actuator",
            "patent_number": "US9988776C",
            "abstract": f"A hydraulic actuator controlling {query} performance precisely.",
            "similarity": 0,
            "url": "https://patents.google.com/patent/US9988776C"
        }
    ]
    return {"results": results}

# ------------------ PDF Download Endpoint ------------------
@app.get("/download")
def download_report(query: str):
    """
    Generates a PDF report from the same mock data.
    """
    results = [
        {
            "title": f"{query.title()} Self-Adjusting Device",
            "patent_number": "US1234567A",
            "abstract": f"A mechanism related to {query} that automatically adjusts for optimal performance.",
            "similarity": 25,
            "url": "https://patents.google.com/patent/US1234567A"
        },
        {
            "title": f"Automatic {query.title()} System",
            "patent_number": "US7654321B",
            "abstract": f"A system designed for {query} to activate automatically under certain conditions.",
            "similarity": 30,
            "url": "https://patents.google.com/patent/US7654321B"
        },
        {
            "title": f"Hydraulic {query.title()} Actuator",
            "patent_number": "US9988776C",
            "abstract": f"A hydraulic actuator controlling {query} performance precisely.",
            "similarity": 0,
            "url": "https://patents.google.com/patent/US9988776C"
        }
    ]

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, "PatentHound Idea Analysis Report")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 80, f"Idea: {query}")
    pdf.drawString(50, height - 100, f"Total Patents: {len(results)}")

    y = height - 140
    for p in results:
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, p["title"])
        y -= 18
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, f"Patent Number: {p['patent_number']}")
        y -= 14
        pdf.drawString(50, y, f"Similarity: {p['similarity']}%")
        y -= 14
        pdf.drawString(50, y, f"Abstract: {p['abstract']}")
        y -= 24
        if y < 100:
            pdf.showPage()
            y = height - 50

    pdf.save()
    buffer.seek(0)
    return FileResponse(buffer, media_type='application/pdf', filename=f"{query}_PatentHound_Report.pdf")
