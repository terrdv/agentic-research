import requests
from langchain_core.tools import tool
from scholarly import scholarly


@tool
def search_google_scholar(query: str, max_results: int = 5) -> str:
    """Search Google Scholar for academic papers on a topic.

    Returns titles, authors, year, abstract snippet, and citation count.
    """
    try:
        results = []
        for i, pub in enumerate(scholarly.search_pubs(query)):
            if i >= max_results:
                break
            bib = pub.get("bib", {})
            results.append(
                {
                    "title": bib.get("title", "N/A"),
                    "authors": bib.get("author", "N/A"),
                    "year": bib.get("pub_year", "N/A"),
                    "abstract": bib.get("abstract", "N/A")[:300],
                    "citations": pub.get("num_citations", 0),
                    "url": pub.get("pub_url", "N/A"),
                }
            )
        if not results:
            return "No results found."
        return "\n\n".join(
            f"[{r['year']}] {r['title']}\n"
            f"Authors: {r['authors']}\n"
            f"Citations: {r['citations']}\n"
            f"Abstract: {r['abstract']}\n"
            f"URL: {r['url']}"
            for r in results
        )
    except Exception as e:
        return f"Google Scholar search failed: {e}"


@tool
def search_semantic_scholar(query: str, max_results: int = 5) -> str:
    """Search Semantic Scholar for academic papers.

    Returns titles, authors, year, abstract snippet, citation count, and links.
    """
    try:
        resp = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": max_results,
                "fields": "title,authors,year,abstract,citationCount,url",
            },
            timeout=10,
        )
        resp.raise_for_status()
        papers = resp.json().get("data", [])
        if not papers:
            return "No results found."
        results = []
        for p in papers:
            authors = ", ".join(a["name"] for a in p.get("authors", []))
            abstract = (p.get("abstract") or "")[:300]
            results.append(
                f"[{p.get('year', 'N/A')}] {p.get('title', 'N/A')}\n"
                f"Authors: {authors}\n"
                f"Citations: {p.get('citationCount', 0)}\n"
                f"Abstract: {abstract}\n"
                f"URL: {p.get('url', 'N/A')}"
            )
        return "\n\n".join(results)
    except Exception as e:
        return f"Semantic Scholar search failed: {e}"


TOOLS = [search_google_scholar, search_semantic_scholar]
