from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
def home():
    return {"message": "PatentHound API running"}

@app.get("/search")
def search(query: str):

    url = "https://api.lens.org/patent/search"

    payload = {
        "query": {
            "match": {
                "title": query
            }
        },
        "size": 10
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(url, json=payload, headers=headers)
        data = r.json()

        results = []

        for item in data.get("data", []):

            results.append({
                "title": item.get("title"),
                "number": item.get("lens_id"),
                "abstract": item.get("abstract")
            })

        return {"results": results}

    except Exception as e:
        return {"error": str(e)}
