from fastapi import FastAPI, Query
import requests

app = FastAPI()

@app.get("/analyze")
def analyze_idea(query: str):
    # 1️⃣ Search Lens API (or US API)
    lens_url = "https://api.lens.org/patents/search"
    headers = {"Authorization": "Bearer YOUR_LENS_KEY"}  # optional for now
    params = {"q": query, "limit":5}
    
    # 2️⃣ Call API
    response = requests.get(lens_url, params=params)
    patents = response.json().get("results", [])

    # 3️⃣ Calculate similarity (simple example using keyword matching)
    results = []
    for p in patents:
        title = p.get("title", "")
        abstract = p.get("abstract", "")
        # naive similarity: count overlapping words
        common_words = set(query.lower().split()) & set((title+abstract).lower().split())
        score = min(len(common_words)*20, 100)  # max 100%
        results.append({
            "title": title,
            "patent_number": p.get("publication_number"),
            "abstract": abstract,
            "similarity": score,
            "url": p.get("url")
        })

    # 4️⃣ Return JSON
    return {"results": results}
