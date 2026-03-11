from fastapi import FastAPI
import requests

app = FastAPI()

BASE_URL = "https://search.patentsview.org/api/v1/patent"

@app.get("/")
def home():
    return {"message": "Patent search API running"}

@app.get("/search")
def search(query: str):
    try:
        # Build query for _text_any on title and abstract
        q = {
            "_or": [
                {"_text_any": {"patent_title": query}},
                {"_text_any": {"patent_abstract": query}}
            ]
        }
        
        params = {
            "q": requests.utils.requote_uri(str(q)),
            "o": '{"per_page": 25}'  # return up to 25 results
        }

        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        patents = []
        for p in data.get("patents", []):
            patents.append({
                "title": p.get("patent_title", ""),
                "abstract": p.get("patent_abstract", ""),
                "number": p.get("patent_id", "")
            })

        return {"patents": patents}

    except Exception as e:
        return {"error": "Something went wrong", "details": str(e)}