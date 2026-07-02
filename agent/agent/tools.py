import io
import re

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from pypdf import PdfReader
from scholarly import scholarly

from config.settings import settings

_HEADERS = {"User-Agent": "Mozilla/5.0 (agentic-research)"}

# Full text is capped to protect the LLM context window / cost.
# ~40k chars is roughly 10k tokens, comfortably within gpt-4o's 128k window.
_MAX_CHARS = 40_000

# arXiv identifier patterns: new-style (e.g. 1706.03762v2) and old-style (e.g. cs.CL/0501001).
_ARXIV_NEW = re.compile(r"\b(\d{4}\.\d{4,5})(v\d+)?\b")
_ARXIV_OLD = re.compile(r"\b([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?\b")

# DOI embedded in a URL or string, e.g. 10.3389/fpsyt.2021.727117
_DOI = re.compile(r"10\.\d{4,9}/[^\s?#]+")
# Trailing publisher path segments that are not part of the DOI itself.
_DOI_SUFFIXES = ("/full", "/pdf", "/abstract", "/meta", "/html", "/epdf")


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
                    "abstract": (bib.get("abstract") or "N/A")[:300],
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
            f"URL: {r['url']}\n"
            f"Fetch: {r['url']}"
            for r in results
        )
    except Exception as e:
        return f"Google Scholar search failed: {e}"


@tool
def search_semantic_scholar(query: str, max_results: int = 5) -> str:
    """Search Semantic Scholar for academic papers.

    Returns titles, authors, year, abstract snippet, citation count, and a
    'Fetch:' handle (arXiv id or open-access PDF URL) that can be passed to
    fetch_paper_content to read the full paper.
    """
    try:
        resp = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "limit": max_results,
                "fields": "title,authors,year,abstract,citationCount,url,externalIds,openAccessPdf",
            },
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        papers = resp.json().get("data", [])
        if not papers:
            return "No results found."
        results = []
        for p in papers:
            authors = ", ".join(a["name"] for a in p.get("authors", []))
            abstract = (p.get("abstract") or "")[:300]
            fetch = _fetch_handle(p)
            results.append(
                f"[{p.get('year', 'N/A')}] {p.get('title', 'N/A')}\n"
                f"Authors: {authors}\n"
                f"Citations: {p.get('citationCount', 0)}\n"
                f"Abstract: {abstract}\n"
                f"URL: {p.get('url', 'N/A')}\n"
                f"Fetch: {fetch}"
            )
        return "\n\n".join(results)
    except Exception as e:
        return f"Semantic Scholar search failed: {e}"


@tool
def fetch_paper_content(paper: str) -> str:
    """Download an academic paper and return its full extracted text.

    Accepts an arXiv id (e.g. '1706.03762'), an arXiv URL, a direct PDF URL, a
    DOI, or a publisher/Semantic Scholar paper URL. Use the 'Fetch:' handle from
    a search result. For paywalled publisher links it automatically tries to find
    a free open-access copy. Handles both PDF and HTML full text.

    Call this to read the full text of a promising paper instead of relying on
    the abstract snippet alone.
    """
    paper = paper.strip()
    candidates = _candidate_urls(paper)
    if not candidates:
        return f"Could not resolve a fetchable source for: {paper}"

    errors: list[str] = []
    for url in candidates:
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            errors.append(f"{url}: {e}")
            continue

        ctype = resp.headers.get("content-type", "").lower()
        if "pdf" in ctype or url.lower().endswith(".pdf"):
            text = _extract_pdf_text(resp.content)
        elif "html" in ctype:
            text = _extract_html_text(resp.text)
        else:
            errors.append(f"{url}: unsupported content-type '{ctype or 'unknown'}'")
            continue

        if text:
            if len(text) > _MAX_CHARS:
                note = f"\n\n[...truncated — showing first {_MAX_CHARS} of {len(text)} characters]"
                text = text[:_MAX_CHARS] + note
            return f"Full text from {url}:\n\n{text}"
        errors.append(f"{url}: no extractable text (scanned image or empty)")

    detail = "; ".join(errors)
    return (
        f"Could not retrieve full text for '{paper}'. This paper is likely paywalled "
        f"with no open-access copy available. Tried: {detail}"
    )


def _candidate_urls(paper: str) -> list[str]:
    """Ordered list of URLs to try, most-likely-to-succeed first."""
    candidates: list[str] = []

    direct = _resolve_pdf_url(paper)
    if direct:
        candidates.append(direct)

    # If the input carries a DOI, ask Unpaywall for a free open-access copy.
    doi = _extract_doi(paper)
    if doi:
        for url in _unpaywall_urls(doi):
            if url not in candidates:
                candidates.append(url)

    # As a last resort, try the original URL as-is (may be open HTML).
    if paper.lower().startswith("http") and paper not in candidates:
        candidates.append(paper)

    return candidates


def _fetch_handle(paper: dict) -> str:
    """Best fetchable handle for a Semantic Scholar search result."""
    arxiv = (paper.get("externalIds") or {}).get("ArXiv")
    if arxiv:
        return arxiv
    oa = paper.get("openAccessPdf") or {}
    if oa.get("url"):
        return oa["url"]
    return paper.get("url", "N/A")


def _resolve_pdf_url(paper: str) -> str | None:
    """Resolve an identifier/URL to a directly downloadable PDF URL."""
    low = paper.lower()

    if low.endswith(".pdf"):
        return paper

    if "arxiv.org" in low or low.startswith("arxiv:"):
        m = _ARXIV_NEW.search(paper) or _ARXIV_OLD.search(paper)
        if m:
            return f"https://arxiv.org/pdf/{m.group(1)}"

    if "semanticscholar.org" in low or low.startswith("corpusid:"):
        return _semantic_scholar_pdf_url(paper)

    # Bare arXiv id, e.g. "1706.03762" or "cs.CL/0501001".
    m = _ARXIV_NEW.fullmatch(paper) or _ARXIV_OLD.fullmatch(paper)
    if m:
        return f"https://arxiv.org/pdf/{m.group(1)}"

    # Generic publisher URLs are handled by _candidate_urls (Unpaywall + raw URL),
    # so we don't treat them as a direct PDF here.
    return None


def _semantic_scholar_pdf_url(paper: str) -> str | None:
    """Look up a paper on Semantic Scholar and return an arXiv or open-access PDF URL."""
    pid = paper
    if "semanticscholar.org/paper/" in paper.lower():
        pid = paper.rstrip("/").split("/")[-1]
    try:
        resp = requests.get(
            f"https://api.semanticscholar.org/graph/v1/paper/{pid}",
            params={"fields": "externalIds,openAccessPdf"},
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return None
    data = resp.json()
    arxiv = (data.get("externalIds") or {}).get("ArXiv")
    if arxiv:
        return f"https://arxiv.org/pdf/{arxiv}"
    return (data.get("openAccessPdf") or {}).get("url")


def _extract_doi(text: str) -> str | None:
    """Pull a DOI out of a URL or string, trimming publisher path suffixes."""
    m = _DOI.search(text)
    if not m:
        return None
    doi = m.group(0).rstrip(".,);]")
    for suffix in _DOI_SUFFIXES:
        if doi.lower().endswith(suffix):
            doi = doi[: -len(suffix)]
            break
    return doi


def _unpaywall_urls(doi: str) -> list[str]:
    """Ask Unpaywall for open-access copies of a DOI; PDF link first, then landing page."""
    email = settings.unpaywall_email
    if not email:
        return []
    try:
        resp = requests.get(
            f"https://api.unpaywall.org/v2/{doi}",
            params={"email": email},
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return []
    loc = resp.json().get("best_oa_location") or {}
    urls = [loc.get("url_for_pdf"), loc.get("url")]
    return [u for u in urls if u]


def _extract_html_text(html: str) -> str:
    """Extract readable body text from an HTML page."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    root = soup.find("article") or soup.body or soup
    text = root.get_text(separator="\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _extract_pdf_text(content: bytes) -> str:
    """Extract and lightly normalise text from PDF bytes."""
    reader = PdfReader(io.BytesIO(content))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    text = "\n".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


TOOLS = [search_google_scholar, search_semantic_scholar, fetch_paper_content]
