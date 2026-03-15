from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/analyze")
def analyze(query: str):

    # Build PatentsView search URL
    base_url = "https://patentsview.org/api/patents/query"
    
    # Simple text search on title or abstract
    q = {
        "_or": [
            {"_text_any":{"patent_title": query}},
            {"_text_any":{"patent_abstract": query}}
        ]
    }
    
    # Which fields we want in the response
    f = ["patent_number","patent_title","patent_abstract"]
    
    params = {
        "q": str(q).replace("'", '"'),  # JSON needs double quotes
        "f": str(f).replace("'", '"'),
        "o": '{"per_page": 10}'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        patents = data.get("patents", [])
    except Exception as e:
        # If anything goes wrong, return empty list
        print("Error fetching patent data:", e)
        patents = []
    
    # Process results
    results = []
    similarities = []
    query_words = set(query.lower().split())
    
    for p in patents:
        title = p.get("patent_title","No title")
        abstract = p.get("patent_abstract","")
        
        combined = (title + " " + abstract).lower()
        text_words = set(combined.split())
        common = query_words.intersection(text_words)
        similarity = min(len(common) * 20, 100)
        similarities.append(similarity)
        
        results.append({
            "title": title,
            "patent_number": p.get("patent_number",""),
            "abstract": abstract,
            "similarity": similarity,
            "url": f"https://patents.google.com/patent/{p.get('patent_number','')}"
        })
    
    # Calculate novelty score
    if similarities:
        avg_sim = sum(similarities)/len(similarities)
    else:
        avg_sim = 0
    novelty_score = round(100 - avg_sim)
    
    return {
        "query": query,
        "novelty_score": novelty_score,
        "average_similarity": avg_sim,
        "results": results
    }
