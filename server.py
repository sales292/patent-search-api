from fastapi import FastAPI
from fastapi.responses import FileResponse
import requests
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = FastAPI()

# ---------- ANALYZE ENDPOINT ----------
@app.get("/analyze")
def analyze_idea(query: str):
    """
    Returns a JSON list of patent results with similarity scores.
    Uses a mock or live API via requests.
    """
    try:
        # Example: call a live patent API (replace with real API if available)
        response = requests.get("https://some-patent-api.com/search", params={"q": query})
        response.raise_for_status()
        data = response.json()
        # Expected format: {"results":[{"title":..., "patent_number":..., "abstract":..., "similarity":..., "url":...}]}
    except:
        # fallback mock data
        data = {"results":[
            {"title": f"{query.title()} Example Patent", 
             "patent_number":"US1234567A", 
             "abstract":"Example abstract describing the invention.", 
             "similarity":25, 
             "url":"https://patents.google.com/patent/US1234567A"},
            {"title": f"Improved {query.title()} Device", 
             "patent_number":"US7654321B", 
             "abstract":"Another example abstract.", 
             "similarity":30, 
             "url":"https://patents.google.com/patent/US7654321B"}
        ]}
    return data

# ---------- DOWNLOAD PDF ENDPOINT ----------
@app.get("/download")
def download_report(query: str):
    """
    Generates a PDF report dynamically based on the idea query and returns it as a file.
    """
    # Use the same mock data as /analyze for demo
    results = [
        {"title": f"{query.title()} Example Patent", 
         "patent_number":"US1234567A", 
         "abstract":"Example abstract describing the invention.", 
         "similarity":25, 
         "url":"https://patents.google.com/patent/US1234567A"},
        {"title": f"Improved {query.title()} Device", 
         "patent_number":"US7654321B", 
         "abstract":"Another example abstract.", 
         "similarity":30, 
         "url":"https://patents.google.com/patent/US7654321B"}
    ]

    # Create PDF in memory
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
