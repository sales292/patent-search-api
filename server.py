from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Patent search API running"}

@app.get("/search")
def search(query: str):
    try:
        url = "https://api.patentsview.org/patents/query"
        params = {
            "q": f'{{"_text_any":{{"patent_title":"{query}"}}}}',
            "f": '["patent_title","patent_number","patent_abstract"]'
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        patents = []
        for p in data.get("patents", [])[:10]:
            patents.append({
                "title": p.get("patent_title",""),
                "abstract": p.get("patent_abstract",""),
                "number": p.get("patent_number","")
            })

        return {"patents": patents}

    except Exception as e:
        return {"error": "Something went wrong", "details": str(e)}