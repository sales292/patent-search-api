from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Patent search API running"}

@app.get("/search")
def search(query: str):
    try:
        url = f"https://api.patentsview.org/patents/query?q={{\"_text_any\":{{\"patent_title\":\"{query}\"}}}}"
        response = requests.get(url, timeout=10)
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