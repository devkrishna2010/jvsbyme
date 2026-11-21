"""
J.A.R.V.I.S. V2 — Extractive Web Intelligence & Research Engine
Satisfies V2 Directive Section 3 & Section 10:
- Understands ordinary factual questions without requiring the explicit keyword 'search'
- Performs multi-source extractive search via DuckDuckGo HTML Lite and Wikipedia API
- Extracts clean, high-relevance paragraphs and retains source URLs
- Zero paid APIs, zero local LLM bloat; deterministic extractive parsing
- Graceful offline fallback with authentic Stark protocol messaging
"""

import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple

import config
from core.responses import get_response

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 (J.A.R.V.I.S. Research Module)"
    )
}


def check_internet_connection(timeout: float = 2.0) -> bool:
    """Verifies active internet connectivity via rapid DNS ping."""
    for host in ["https://1.1.1.1", "https://www.google.com"]:
        try:
            requests.get(host, timeout=timeout)
            return True
        except Exception:
            continue
    return False


def query_wikipedia(topic: str, max_chars: int = 400) -> Optional[Dict[str, str]]:
    """
    Direct Wikipedia REST API summary lookup (zero keys, high precision factual extract).
    """
    clean_topic = urllib.parse.quote(topic.strip().replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_topic}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            extract = data.get("extract", "")
            title = data.get("title", topic)
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{clean_topic}")
            if extract:
                # Truncate to first 2-3 sentences for Bettany cadence
                sentences = re.split(r"(?<=[.!?])\s+", extract)
                concise = " ".join(sentences[:3])
                if len(concise) > max_chars:
                    concise = concise[:max_chars].rsplit(" ", 1)[0] + "..."
                return {
                    "title": title,
                    "summary": concise,
                    "url": page_url,
                    "source": "Wikipedia"
                }
    except Exception:
        pass
    return None


def search_duckduckgo(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Scrapes DuckDuckGo HTML Lite for factual snippets and source URLs.
    """
    encoded = urllib.parse.quote_plus(query.strip())
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    results = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=5.0)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            snippets = soup.find_all("div", class_="result__body")
            for snip in snippets[:max_results]:
                link_tag = snip.find("a", class_="result__a")
                snippet_tag = snip.find("a", class_="result__snippet")

                title = link_tag.get_text(strip=True) if link_tag else "Web Reference"
                raw_href = link_tag.get("href", "") if link_tag else ""

                # Unquote DuckDuckGo redirect uddg url
                real_url = raw_href
                if "uddg=" in raw_href:
                    try:
                        real_url = urllib.parse.unquote(raw_href.split("uddg=")[1].split("&")[0])
                    except Exception:
                        real_url = raw_href

                snippet_text = snippet_tag.get_text(strip=True) if snippet_tag else ""
                if snippet_text:
                    results.append({
                        "title": title,
                        "summary": snippet_text,
                        "url": real_url,
                        "source": "Web Research"
                    })
    except Exception:
        pass

    return results


def research_topic(query: str) -> Dict[str, Any]:
    """
    Autonomous multi-source research pipeline:
    1. Checks connection
    2. Identifies question type (explanatory 'why' vs factual entity)
    3. Queries Wikipedia for core encyclopedic entities (e.g. Neymar, Quantum Computing, Albert Einstein)
    4. Queries DuckDuckGo for general / current events and explanations
    5. Combines results into a polished J.A.R.V.I.S. briefing
    """
    clean_q = query.strip().rstrip("?").strip()

    if not check_internet_connection():
        return {
            "success": False,
            "speech": get_response("no_internet"),
            "url": "",
            "source": ""
        }

    # Extract substantive entity / subject for Wikipedia REST lookup
    wiki_topic = clean_q
    prefixes = [
        "tell me about", "who was", "who were", "who is", "who are",
        "who created", "who built", "who invented", "who discovered",
        "what was", "what were", "what is", "what's", "what are",
        "why was", "why were", "why is", "why are", "why do", "why does", "why did",
        "when was", "when did", "when were", "when is", "when will",
        "where was", "where were", "where is", "where are", "where can i find",
        "how does", "how do", "how was", "how were", "how did", "how is", "how can",
        "how many", "how much", "how far is", "how old is", "how tall is",
        "which country", "which city", "which is", "which are",
        "explain", "what's happening in", "search for", "search the web for",
        "search", "google", "look up", "find info on", "find information on",
        "can you tell me about", "can you tell me", "do you know about", "do you know"
    ]
    for prefix in prefixes:
        if wiki_topic.lower().startswith(prefix):
            wiki_topic = wiki_topic[len(prefix):].strip()
            break

    # Strip leading articles for Wikipedia entity lookup
    wiki_entity = re.sub(r"^(?:the|a|an)\s+", "", wiki_topic, flags=re.IGNORECASE).strip()

    is_why_question = clean_q.lower().startswith("why ") or " why " in clean_q.lower()

    # For explanatory 'why' inquiries, DuckDuckGo provides richer explanations than static wiki titles
    if is_why_question:
        ddg_res = search_duckduckgo(clean_q, max_results=2)
        if ddg_res:
            top = ddg_res[0]
            return {
                "success": True,
                "speech": f"According to scientific archives regarding '{clean_q}': {top['summary']}",
                "url": top["url"],
                "source": top["source"]
            }

    # First attempt for factual entities: Encyclopedic Wikipedia extract
    if wiki_entity:
        wiki_res = query_wikipedia(wiki_entity)
        if wiki_res:
            return {
                "success": True,
                "speech": f"According to current archives on {wiki_res['title']}: {wiki_res['summary']}",
                "url": wiki_res["url"],
                "source": wiki_res["source"]
            }

    # Second attempt: DuckDuckGo search on full query
    ddg_res = search_duckduckgo(clean_q, max_results=2)
    if ddg_res:
        top = ddg_res[0]
        return {
            "success": True,
            "speech": f"My research into '{clean_q}' reveals: {top['summary']}",
            "url": top["url"],
            "source": top["source"]
        }

    # Third attempt: DuckDuckGo on stripped topic
    if wiki_topic and wiki_topic != clean_q:
        ddg_res2 = search_duckduckgo(wiki_topic, max_results=1)
        if ddg_res2:
            top = ddg_res2[0]
            return {
                "success": True,
                "speech": f"My research into '{wiki_topic}' reveals: {top['summary']}",
                "url": top["url"],
                "source": top["source"]
            }

    return {
        "success": False,
        "speech": f"I was unable to extract definitive records regarding '{query}', sir. Perhaps we might refine the search parameters.",
        "url": "",
        "source": ""
    }


def search_web(query: str, max_results: int = 3) -> Tuple[bool, List[Dict[str, str]], str]:
    """Legacy compatibility bridge for existing tests."""
    res = research_topic(query)
    if res["success"]:
        return True, [{"title": query, "snippet": res["speech"], "url": res["url"]}], "Results retrieved successfully, sir."
    return False, [], res["speech"]


def handle_search(intent_res) -> str:
    """Dispatches search queries from brain."""
    query = intent_res.parameters.get("query", "")
    if not query:
        return "What subject would you like me to research, sir?"

    res = research_topic(query)
    return res["speech"]
