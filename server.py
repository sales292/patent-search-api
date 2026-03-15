from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Allow your website to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later replace with https://patenthound.co.uk
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "PatentHound API running"}

@app.get("/analyze")
def analyze(query: str):

    # For now we simulate some patent results
    patents = [
        {
            "title": "Self adjusting bicycle brake",
            "patent_number": "US1234567A",
            "abstract": "Brake mechanism that automatically adjusts tension."
        },
        {
            "title": "Automatic bicycle braking system",
            "patent_number": "US7654321B",
            "abstract": "System that activates bicycle brakes automatically."
        },
        {
            "title": "Hydraulic brake actuator",
            "patent_number": "US9988776C",
            "abstract": "Hydraulic actuator controlling braking pressure."
        }
    ]

    results = []
    similarities = []

    query_words = set(query.lower().split())

    for p in patents:

        title = p["title"]
        abstract = p["abstract"]

        text_words = set((title + " " + abstract).lower().split())

        common_words = query_words.intersection(text_words)

        similarity = min(len(common_words) * 20, 100)

        similarities.append(similarity)

        results.append({
            "title": title,
            "patent_number": p["patent_number"],
            "abstract": abstract,
            "similarity": similarity,
            "url": f"https://patents.google.com/?q={query.replace(' ','+')}"
        })

    # Calculate novelty score
    if similarities:
        avg_similarity = sum(similarities) / len(similarities)
    else:
        avg_similarity = 0

    novelty_score = round(100 - avg_similarity)

    return {
        "query": query,
        "novelty_score": novelty_score,
        "average_similarity": avg_similarity,
        "results": results
    }
