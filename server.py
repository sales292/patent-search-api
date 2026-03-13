from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Allow calls from your WordPress site
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your domain if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/analyze")
def analyze_idea(query: str = Query(..., description="Keyword to search patents")):
    """
    Fetch real US patents from PatentsView API.
    """
    base_url = "https://api.patentsview.org/patents/query"
    
    # Construct query for title or abstract containing the keyword
    # "_text_any" searches multiple fields
    api_query = {
        "_or": [
            {"_text_any": {"patent_title": query}},
            {"_text_any": {"patent_abstract": query}}
        ]
    }
    
    # Fields we want to retrieve
    fields = ["patent_title", "patent_number", "patent_abstract"]

    try:
        response = requests.get(
            base_url,
            params={
                "q": str(api_query),
                "f": str(fields),
                "o": '{"per_page":5}'  # return top 5 patents
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        patents = data.get("patents", [])

        # Build results for front-end
        results = []
        for p in patents:
            title = p.get("patent_title", "No Title")
            number = p.get("patent_number", "")
            abstract = p.get("patent_abstract", "No Abstract")
            url = f"https://patents.google.com/patent/{number}"
            
            # Simple similarity: count overlap of query words in title/abstract
            common_words = set(query.lower().split()) & set((title + " " + abstract).lower().split())
            similarity = min(len(common_words) * 20, 100)  # max 100%

            results.append({
                "title": title,
                "patent_number": number,
                "abstract": abstract,
                "similarity": similarity,
                "url": url
            })

        return {"results": results}

    except requests.RequestException as e:
