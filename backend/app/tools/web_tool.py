from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus

# NOTE:
# - Stage 6 allows cached web results for reliability in demo environments.
# - We keep an optional live DuckDuckGo fetch, but cached results are preferred.

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    requests = None
    BeautifulSoup = None


CACHE_PATH = Path(__file__).with_name("web_cache.json")


@dataclass
class WebResult:
    title: str
    url: str
    snippet: str


def _load_cache() -> Dict[str, List[Dict[str, str]]]:
    if not CACHE_PATH.exists():
        return {}
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_query(q: str) -> str:
    return " ".join((q or "").strip().lower().split())


def _cached_search(query: str, max_results: int) -> List[WebResult]:
    cache = _load_cache()
    qn = _normalize_query(query)

    # direct hit
    if qn in cache:
        return [WebResult(**r) for r in cache[qn][:max_results]]

    # fuzzy contains match
    for key, items in cache.items():
        if key in qn or qn in key:
            return [WebResult(**r) for r in items[:max_results]]

    return []


def _ua_headers() -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }


def _parse_ddg_html(html: str, max_results: int) -> List[WebResult]:
    if BeautifulSoup is None:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results: List[WebResult] = []

    for res in soup.select(".result"):
        a = res.select_one("a.result__a")
        snip = res.select_one(".result__snippet")
        if not a:
            continue

        title = a.get_text(" ", strip=True)
        href = (a.get("href") or "").strip()
        snippet = snip.get_text(" ", strip=True) if snip else ""

        if not href.startswith("http"):
            continue

        results.append(WebResult(title=title, url=href, snippet=snippet))
        if len(results) >= max_results:
            break

    return results


def _live_ddg_search(query: str, max_results: int, timeout_s: int = 20) -> List[WebResult]:
    # optional live mode (may be blocked on some networks)
    if requests is None:
        return []

    q = (query or "").strip()
    if not q:
        return []

    url = f"https://duckduckgo.com/html/?q={quote_plus(q)}"
    r = requests.get(url, headers=_ua_headers(), timeout=timeout_s)
    r.raise_for_status()
    return _parse_ddg_html(r.text, max_results=max_results)


class WebTool:
    name = "web"
    description = "Web search (cached-first for reliability) returning snippets + URLs."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "default": 5},
            "mode": {"type": "string", "default": "cached"},  # cached | live | auto
        },
        "required": ["query"],
    }

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.perf_counter()

        query = (input.get("query") or "").strip()
        max_results = int(input.get("max_results", 5))
        mode = (input.get("mode") or "cached").strip().lower()

        results: List[WebResult] = []
        used_mode = mode

        if mode in ("cached", "auto"):
            results = _cached_search(query, max_results=max_results)
            used_mode = "cached"

        if (not results) and mode in ("live", "auto"):
            results = _live_ddg_search(query, max_results=max_results)
            used_mode = "live"

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "query": query,
            "mode": used_mode,
            "results": [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results],
            "count": len(results),
            "elapsed_ms": elapsed_ms,
        }
