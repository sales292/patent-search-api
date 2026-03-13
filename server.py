from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

# Allow your website to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "PatentHound API running"}

@app.get("/analyze")
def analyze(query: str):

    # Create dynamic results based on the search keyword
    results = [
        {
            "title": f"{query.title()} Mechanical System",
            "patent_number": f"US{random.randint(1000000,9999999)}A",
            "abstract": f"A system relating to {query} technology and mechanical design.",
            "similarity": random.randint(20,80),
            "url": f"https://patents.google.com/?q={query}"
        },
        {
            "title": f"Improved {query.title()} Device",
            "patent_number": f"US{random.randint(1000000,9999999)}B",
            "abstract": f"A device designed to improve the efficiency of {query}.",
            "similarity": random.randint(10,60),
            "url": f"https://patents.google.com/?q={query}"
        },
        {
            "title": f"{query.title()} Control Mechanism",
            "patent_number": f"US{random.randint(1000000,9999999)}C",
            "abstract": f"A control mechanism related to {query} functionality.",
            "similarity": random.randint(5,50),
            "url": f"https://patents.google.com/?q={query}"
        }
    ]

    return {"results": results}
