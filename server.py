from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/analyze")
def analyze(query: str):

    results = [
        {"title": f"{query} system A", "abstract": "Test patent A", "similarity": 40},
        {"title": f"{query} system B", "abstract": "Test patent B", "similarity": 30},
        {"title": f"{query} system C", "abstract": "Test patent C", "similarity": 20}
    ]

    avg = sum(r["similarity"] for r in results) / len(results)
    novelty = round(100 - avg)

    return {
        "query": query,
        "novelty": novelty,
        "risk": "Medium",
        "results": results
