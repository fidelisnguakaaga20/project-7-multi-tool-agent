import time
import re
from typing import Any, Dict, List, Optional

from app.agent.llm import llm_reply  # fallback only
from app.tools.calculator import calculator_tool

# Stage 4 imports (RAG)
from app.rag.embeddings import embed_texts
from app.rag.store import get_chroma_collection

# Stage 5 imports (SQL)
from app.tools.sql_tool import SQLTool

# Stage 6 imports (WEB)
from app.tools.web_tool import WebTool

# Stage 7 planner (now memory-aware)
from app.agent.planner import make_plan

# Stage 8 memory
from app.agent.memory import (
    get_state,
    update_state,
    extract_preferences_from_user_message,
    update_retrieved_sources,
)

sql_tool = SQLTool()
web_tool = WebTool()


def _format_citations(passages: list[dict]) -> List[str]:
    """
    Return citations as list[str] (Stage 8+).
    """
    cites: List[str] = []
    for p in passages:
        src = (p.get("source") or "unknown").strip()
        cid = (p.get("chunk_id") or "unknown").strip()
        if "#" in cid:
            cites.append(f"[{cid}]")
        else:
            cites.append(f"[{src}#{cid}]")

    # de-dupe keep order
    seen = set()
    uniq = []
    for c in cites:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def _run_rag(query: str, top_k: int = 4) -> Dict[str, Any]:
    col = get_chroma_collection()
    q_emb = embed_texts([query])[0]

    res = col.query(
        query_embeddings=[q_emb],
        n_results=int(top_k),
        include=["documents", "metadatas", "distances"],
    )

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    ids = res.get("ids", [[]])[0]
    dists = res.get("distances", [[]])[0]

    passages: list[dict] = []
    for doc, meta, cid, dist in zip(docs, metas, ids, dists):
        passages.append(
            {
                "chunk_id": cid,
                "source": (meta or {}).get("source", "unknown"),
                "page": (meta or {}).get("page", None),
                "distance": dist,
                "text_preview": (doc[:220] + "...") if doc and len(doc) > 220 else doc,
                "text": doc,
            }
        )

    return {"passages": passages}


def _run_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    return web_tool.run({"query": query, "max_results": max_results, "mode": "cached"})


def _deterministic_sql_from_question(question: str) -> str:
    q = (question or "").lower()

    m_top = re.search(r"top\s+(\d+)", q)
    limit = int(m_top.group(1)) if m_top else 5

    if "customer" in q and "order" in q and ("top" in q or "most" in q):
        return f"""
SELECT c.id, c.name, COUNT(o.id) AS total_orders
FROM customers c
JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.name
ORDER BY total_orders DESC
LIMIT {limit}
        """.strip()

    if "customer" in q and ("spent" in q or "revenue" in q or "total amount" in q) and ("top" in q or "most" in q):
        return f"""
SELECT c.id, c.name, COALESCE(SUM(o.total_amount), 0) AS total_spent
FROM customers c
JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.name
ORDER BY total_spent DESC
LIMIT {limit}
        """.strip()

    if "ticket" in q and ("status" in q or "open" in q or "closed" in q):
        return """
SELECT status, COUNT(*) AS total
FROM tickets
GROUP BY status
ORDER BY total DESC
LIMIT 50
        """.strip()

    raise ValueError(
        "No SQL template matched. Try: 'Show top 5 customers by total orders' or 'Top 3 customers by total spent'."
    )


def _run_sql(question: str) -> Dict[str, Any]:
    sql = _deterministic_sql_from_question(question)
    return sql_tool.run({"sql": sql})


def _run_calculator(expression: str) -> Dict[str, Any]:
    return calculator_tool({"expression": expression})


def run_agent(message: str, conversation_id: str | None = None) -> dict:
    trace: list[dict] = []
    citations: List[str] = []
    thoughtless_plan: List[str] = []

    # Stage 8: update memory from user preference statements
    if conversation_id:
        pref_patch = extract_preferences_from_user_message(message)
        if pref_patch:
            update_state(conversation_id, pref_patch)

    mem_state = get_state(conversation_id) if conversation_id else {}

    plan_obj = make_plan(message, memory_state=mem_state)
    thoughtless_plan = plan_obj.get("thoughtless_plan", []) or []
    calls: List[Dict[str, Any]] = plan_obj.get("calls", []) or []
    calls = calls[:4]

    rag_passages: List[Dict[str, Any]] = []
    rag_citations: List[str] = []
    web_results: List[Dict[str, Any]] = []
    sql_out: Dict[str, Any] | None = None
    calc_out: Dict[str, Any] | None = None

    for call in calls:
        tool = (call.get("tool") or "").strip()
        tool_input = call.get("input") or {}

        t0 = time.perf_counter()
        try:
            if tool == "rag":
                out = _run_rag(tool_input.get("query", message), top_k=int(tool_input.get("top_k", 4)))
                rag_passages = out.get("passages", [])
                rag_citations = _format_citations(rag_passages[:3])
                citations.extend(rag_citations)

                # Stage 8: store last retrieved sources
                if conversation_id:
                    srcs = []
                    for p in rag_passages[:10]:
                        srcs.append(str(p.get("source", "unknown")))
                    update_retrieved_sources(conversation_id, srcs)

                out_summary = f"matches={len(rag_passages)}"

            elif tool == "sql":
                out = _run_sql(tool_input.get("question", message))
                sql_out = out
                out_summary = f"row_count={out.get('row_count')}"

            elif tool == "calculator":
                out = _run_calculator(tool_input.get("expression", ""))
                calc_out = out
                out_summary = f"result={out.get('result')}"

            elif tool == "web":
                out = _run_web(tool_input.get("query", message), max_results=int(tool_input.get("max_results", 5)))
                web_results = out.get("results", [])
                out_summary = f"mode={out.get('mode')} results={out.get('count')}"

            else:
                out_summary = "skipped"

            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            trace.append({"tool": tool, "input": tool_input, "output_summary": out_summary, "elapsed_ms": elapsed_ms})

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            trace.append({"tool": tool, "input": tool_input, "output_summary": f"ERROR: {str(e)}", "elapsed_ms": elapsed_ms})

    # Build final answer
    parts: List[str] = []

    if rag_passages:
        top = rag_passages[:3]
        snips = "\n".join([f"- ({p['source']} p{p['page']}) {p['text_preview']}" for p in top])
        parts.append("From your documents:\n" + snips)

    if sql_out:
        cols = sql_out.get("columns", [])
        rows = (sql_out.get("rows", []) or [])[:5]
        lines = []
        lines.append("From the database:")
        lines.append(f"SQL used: {sql_out.get('sql')}")
        if cols and rows:
            lines.append(" | ".join(cols))
            lines.append("-" * 60)
            for r in rows:
                lines.append(" | ".join([str(r.get(c, "")) for c in cols]))
        else:
            lines.append("No rows returned.")
        parts.append("\n".join(lines))

    if calc_out is not None:
        parts.append(f"Calculation result: {calc_out.get('result')}")

    if web_results:
        lines = ["From web (cached):"]
        for i, r in enumerate(web_results[:5], start=1):
            lines.append(f"{i}. {r.get('title')}\n   {r.get('url')}\n   {r.get('snippet')}")
        parts.append("\n".join(lines))

    if not parts:
        # fallback
        return {
            "answer": llm_reply(message),
            "trace": trace,
            "citations": [],
            "thoughtless_plan": thoughtless_plan,
        }

    return {
        "answer": "\n\n".join(parts),
        "trace": trace,
        "citations": citations,  # /// Stage 8: separate field
        "thoughtless_plan": thoughtless_plan,  # /// Stage 8: return planner steps
    }
