import re

_CALC_HINTS = [
    "calculate",
    "calc",
    "what is",
    "solve",
    "evaluate",
    "math",
    "+",
    "-",
    "*",
    "/",
]

_RAG_HINTS = [
    "according to",
    "in the document",
    "in the doc",
    "in my doc",
    "in my docs",
    "in the pdf",
    "from the pdf",
    "from my pdf",
    "in resume",
    "resume.pdf",
    "policy",
    "as stated",
    "as written",
    "what does the document say",
    "what does my document say",
]

# /// Stage 5: SQL routing hints
_SQL_HINTS = [
    "sql",
    "database",
    "db",
    "sqlite",
    "table",
    "schema",
    "customers",
    "orders",
    "tickets",
    "top",
    "total",
    "sum",
    "count",
    "group by",
    "join",
    "revenue",
    "spent",
]

# /// Stage 6: Web routing hints
_WEB_HINTS = [
    "latest",
    "today",
    "news",
    "current",
    "recent",
    "search web",
    "web search",
    "google",
    "online",
    "internet",
    "what's new",
    "what is new",
]

# /// capture first math expression like: 12*19, 10 + 5 / 2, (3+4)*9
_MATH_EXPR_RE = re.compile(
    r"(\(?\s*\d+(?:\.\d+)?\s*\)?\s*(?:[\+\-\*\/]\s*\(?\s*\d+(?:\.\d+)?\s*\)?\s*)+)"
)


def _extract_expression(message: str) -> str | None:
    """
    Extract ONLY the first math expression from a mixed sentence.
    Example: '... calculate 12*19. Also show top 3 ...' -> '12*19'
    """
    text = (message or "").strip()
    m = _MATH_EXPR_RE.search(text)
    if not m:
        return None

    expr = m.group(1)

    # keep only safe chars
    expr = re.sub(r"[^0-9\.\+\-\*\/\(\)\s]", "", expr).strip()
    return expr if expr else None


def _looks_like_rag(message: str) -> bool:
    msg = message.lower()
    return any(h in msg for h in _RAG_HINTS)


def _looks_like_sql(message: str) -> bool:
    msg = message.lower()
    return any(h in msg for h in _SQL_HINTS)


def _looks_like_web(message: str) -> bool:
    msg = message.lower()
    return any(h in msg for h in _WEB_HINTS)


def _clean_web_query(message: str) -> str:
    q = message.strip()
    q = re.sub(r"^(search\s*web|web\s*search|google)\s*[:\-]\s*", "", q, flags=re.I).strip()
    return q


def pick_tool(message: str) -> tuple[str | None, dict]:
    msg = message.lower().strip()

    # Stage 4: prefer RAG when user hints it's in docs
    if _looks_like_rag(message):
        return "rag", {"query": message, "top_k": 4}

    # Stage 6: Web search
    if _looks_like_web(message):
        return "web", {"query": _clean_web_query(message), "max_results": 5, "mode": "cached"}

    # Stage 5: SQL
    if _looks_like_sql(message):
        return "sql", {"question": message}

    # Calculator: if expression exists, route
    expr = _extract_expression(message)
    if expr:
        return "calculator", {"expression": expr}

    # Hints fallback
    if any(h in msg for h in _CALC_HINTS):
        expr2 = _extract_expression(message)
        if expr2:
            return "calculator", {"expression": expr2}

    return None, {}
