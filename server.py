Python 3.14.3 (v3.14.3:323c59a5e34, Feb  3 2026, 11:41:37) [Clang 16.0.0 (clang-1600.0.26.6)] on darwin
Enter "help" below or click "Help" above for more information.
>>> from fastapi import FastAPI
... import requests
... 
... app = FastAPI()
... 
... @app.get("/")
... def home():
...     return {"message": "Patent search API running"}
... 
... @app.get("/search")
... def search(query: str):
... 
...     url = f"https://api.patentsview.org/patents/query?q={{\"_text_any\":{{\"patent_title\":\"{query}\"}}}}"
... 
...     response = requests.get(url)
...     data = response.json()
... 
...     patents = []
... 
...     for p in data["patents"][:10]:
...         patents.append({
...             "title": p["patent_title"],
...             "abstract": p.get("patent_abstract",""),
...             "number": p["patent_number"]
...         })
... 
