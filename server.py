from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

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
    return {"message": "PatentHound API running"}

@app.get("/analyze")
def analyze(query: str):

    results = [
        {
            "title": f"{query.title()} Mechanical System",
            "patent_number": f"US{random.randint(1000000,9999999)}A",
            "abstract": f"A system relating to {query} technology.",
            "similarity": random.randint(20,80),
            "url": f"https://patents.google.com/?q={query}"
        },
        {
            "title": f"Improved {query.title()} Device",
            "patent_number": f"US{random.randint(1000000,9999999)}B",
            "abstract": f"A device designed to improve {query}.",
            "similarity": random.randint(10,60),
            "url": f"https://patents.google.com/?q={query}"
        }
    ]

    return {"results": results}
