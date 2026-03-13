from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow your WordPress site to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "PatentHound API running"}

@app.get("/analyze")
def analyze(query: str = Query(..., description="Idea to check against patents")):

    # Example patent data (mock for testing)
    patents = [
        {
            "title": "Self adjusting bicycle brake",
            "number": "US1234567A",
            "abstract": "Brake mechanism that automatically adjusts tension."
        },
        {
            "title": "Automatic bicycle braking system",
            "number": "US7654321B",
            "abstract": "System that activates bicycle brakes automatically."
        },
        {
            "title": "Hydraulic brake actuator",
            "number": "US9988776C",
            "abstract": "Hydraulic actuator controlling braking pressure."
        }
    ]

    results = []

    for patent in patents:
        title = patent["title"]
        abstract = patent["abstract"]
        number = patent["number"]

        # Similarity score (simple keyword overlap)
        query_words = set(query.lower().split())
        patent_words = set((title + " " + abstract).lower().split())
        similarity = min(len(query_words & patent_words) * 25, 100)

        # Google Patents URL (always works)
        url = f"https://patents.google.com/patent/{number}"

        results.append({
            "title": title,
            "patent_number": number,
            "abstract": abstract,
            "similarity": similarity,
            "url": url
        })

    return {"results": results}
