from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Patent Search API running"}

@app.get("/search")
def search(query: str):
    url = "https://search.patentsview.org/api/v1/patent"

    # Search both title AND abstract to increase matches
    payload = {
        "q": {
            "_or": [
                {"_text_any": {"patent_title": query}},
                {"_text_any": {"patent_abstract": query}}
            ]
        },
        "f": ["patent_title", "patent_abstract", "patent_id"],
        "o": {"per_page": 10}
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()

        results = []
        for p in data.get("patents", []):
            results.append({
                "title": p.get("patent_title"),
                "number": p.get("patent_id"),
                "abstract": p.get("patent_abstract")
            })

        return {"results": results}

    except Exception as e:
        return {"error": str(e)}
