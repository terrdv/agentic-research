import base64
import hashlib
import hmac
from datetime import datetime, timezone

import requests
from langchain_core.tools import tool
from scholarly import scholarly

from config.settings import settings


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
def search_ubc_library(query: str, max_results: int = 5) -> str:
    """Search UBC Library (Summon) for academic papers, books, and journals.

    Returns titles, authors, publication info, and links.
    Requires UBC_SUMMON_ID and UBC_SUMMON_KEY in environment.
    """
    if not settings.ubc_summon_id or not settings.ubc_summon_key:
        return "UBC Library search unavailable: set UBC_SUMMON_ID and UBC_SUMMON_KEY in .env"

    host = "api.summon.serialssolutions.com"
    path = "/2.0.0/search"
    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    accept = "application/json"

    string_to_sign = "\n".join([accept, date, host, path, f"s.q={query}"])
    digest = hmac.new(
        settings.ubc_summon_key.encode(),
        string_to_sign.encode(),
        hashlib.sha1,
    ).digest()
    signature = base64.b64encode(digest).decode()

    headers = {
        "Accept": accept,
        "x-summon-date": date,
        "Authorization": f"Summon {settings.ubc_summon_id};{signature}",
        "Host": host,
    }

    try:
        resp = requests.get(
            f"https://{host}{path}",
            headers=headers,
            params={"s.q": query, "s.ps": max_results},
            timeout=10,
        )
        resp.raise_for_status()
        docs = resp.json().get("documents", [])
        if not docs:
            return "No results found."
        results = []
        for doc in docs:
            year = (doc.get("PublicationDate_xml") or [{}])[0].get("year", "N/A")
            title = (doc.get("Title") or ["N/A"])[0]
            source = (doc.get("PublicationTitle") or ["N/A"])[0]
            link = doc.get("link", "N/A")
            authors = ", ".join(
                a.get("fullname", "") for a in (doc.get("Author_xml") or [])
            )
            results.append(f"[{year}] {title}\nAuthors: {authors}\nSource: {source}\nLink: {link}")
        return "\n\n".join(results)
    except Exception as e:
        return f"UBC Library search failed: {e}"


TOOLS = [search_google_scholar, search_ubc_library]
