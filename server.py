from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "PatentHound API running"}

@app.get("/analyze")
def analyze(query: str):
    base_url = "https://patentsview.org/api/patents/query"

    # Build safe JSON query
    q = {
        "_or": [
            {"_text_any": {"patent_title": query}},
            {"_text_any": {"patent_abstract": query}}
        ]
    }

    fields = ["patent_number","patent_title","patent_abstract"]
    options = {"per_page":10}

    params = {
        "q": json.dumps(q),       # safely encode JSON
        "f": json.dumps(fields),
        "o": json.dumps(options)
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        patents = data.get("patents", [])
    except Exception as e:
        print("Error fetching patents:", e)
        patents = []

    results = []
    similarities = []
    query_words = set(query.lower().split())

    for p in patents:
        title = p.get("patent_title", "")
        abstract = p.get("patent_abstract", "")
        combined_text = (title + " " + abstract).lower()
        text_words = set(combined_text.split())
        common_words = query_words.intersection(text_words)
        similarity = min(len
