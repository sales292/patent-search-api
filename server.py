from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Patent search API running"}

@app.get("/search")
def search(query: str):

    url = "https://developer.uspto.gov/ibd-api/v1/application/grants"

    params = {
        "searchText": query,
        "rows": 10
    }

    try:
        r = requests.get(url, params=params)
        data = r.json()

        results = []

        for item in data.get("results", []):
            results.append({
                "title": item.get("inventionTitle"),
                "patent_number": item.get("patentNumber"),
                "abstract": item.get("abstractText")
            })

        return {"results": results}

    except Exception as e:
        return {"error": str(e)}
