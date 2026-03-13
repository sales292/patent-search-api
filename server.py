from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow your website to access the API
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

    # Test patents (temporary data)
    patents = [
        {
            "title": "Self adjusting bicycle brake",
            "number": "US1234567A",
            "abstract": "Brake mechanism that automatically adjusts tension.",
            "url": "https://www.lens.org/lens/patent/US1234567A"
        },
        {
            "title": "Automatic bicycle braking system",
            "number": "US7654321B",
            "abstract": "System that activates bicycle brakes automatically.",
            "url": "https://www.lens.org/lens/patent/US7654321B"
        },
        {
            "title": "Hydraulic brake actuator",
            "number": "US9988776C",
            "abstract": "Hydraulic actuator controlling braking pressure.",
            "url": "https://www.lens.org/lens/patent/US9988776C"
        }
    ]

    results = []

    for patent in patents:
        title = patent["title"]
        abstract = patent["abstract"]

        query_words = set(query.lower().split())
        patent_words = set((title + " " + abstract).lower().split())

        matches = query_words & patent_words
        similarity = min(len(matches) * 25, 100)

        results.append({
            "title": title,
            "patent_number": patent["number"],
            "abstract": abstract,
            "similarity": similarity,
            "url": patent["url"]
        })

    return {"results": results}
