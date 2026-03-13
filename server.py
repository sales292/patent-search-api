from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

# Allow your WordPress site to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/analyze")
def analyze_idea(query: str = Query(..., description="Keyword or idea to analyze")):
    """
    Mock analyze endpoint that dynamically returns patent-like results based on the query.
    """

    # Simulate 3 patents with varying similarity
    results = []
    for i in range(1, 4):
        similarity = random.randint(0, 100)
        results.append({
            "title": f"{query.title()} Patent Example {i}",
            "patent_number": f"US{random.randint(1000000, 9999999)}A",
            "abstract": f"This is a mock abstract describing {query} invention example {i}.",
            "similarity": similarity,
            "url": f"https://patents.google.com/patent/US{random.randint(1000000,9999999)}A"
        })

    return {"results": results}
