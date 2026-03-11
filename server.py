from fastapi import FastAPI
import requests
app = FastAPI()

@app.get("/")
def home():
    return {"message": "USPTO Patent Search API running"}

@app.get("/search")
def search(keyword: str):
    """
    Search U.S. patents using USPTO Open Data API.
    Returns JSON with title, patent number, abstract.
    """

    # USPTO Open Data endpoint for granted patents
    url = "https://developer.uspto.gov/ibd-api/v1/application/publications"

    params = {
        "searchText": keyword,
        "rows": 10,          # number of results
        "start": 0           # pagination start
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("inventionTitle"),
                "number": item.get("patentNumber"),
                "abstract": item.get("abstractText")
            })

        return {"results": results}

    except Exception as e:
        return {"error": True, "message": str(e)}
