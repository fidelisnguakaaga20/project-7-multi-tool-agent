import re
from typing import Any, Dict, List, Optional

from app.agent.router import (
    _looks_like_rag,
    _looks_like_sql,
    _looks_like_web,
    _extract_expression,
)

_MATH_PATTERN = re.compile(r"\d\s*[\+\-\*\/]\s*\d")


def make_plan(user_message: str, memory_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Stage 8: planner now considers memory:
    - if prefer_rag_first=True, we try RAG first even when hints are weak
    """
    msg = (user_message or "").strip()
    memory_state = memory_state or {}

    plan: List[str] = []
    calls: List[Dict[str, Any]] = []

    prefer_rag_first = bool(memory_state.get("prefer_rag_first", False))

    # 1) RAG (docs first rule)
    if _looks_like_rag(msg) or prefer_rag_first:
        plan.append("Check user documents for relevant information (docs-first preference).")
        calls.append({"tool": "rag", "input": {"query": msg, "top_k": 4}})

    # 2) SQL
    if _looks_like_sql(msg):
        plan.append("Query the local database for the requested information.")
        calls.append({"tool": "sql", "input": {"question": msg}})

    # 3) Calculator
    expr = _extract_expression(msg)
    if expr and _MATH_PATTERN.search(expr):
        plan.append("Compute the requested calculation.")
        calls.append({"tool": "calculator", "input": {"expression": expr}})

    # 4) Web
    if _looks_like_web(msg):
        plan.append("Search cached web sources for relevant updates.")
        calls.append({"tool": "web", "input": {"query": msg, "max_results": 5, "mode": "cached"}})

    # cap
    calls = calls[:4]

    if not calls:
        plan = ["Answer directly without tools."]
        calls = []

    return {"thoughtless_plan": plan, "calls": calls}
