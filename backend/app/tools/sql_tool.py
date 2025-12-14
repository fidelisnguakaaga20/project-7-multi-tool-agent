# /// Stage 5: SQL tool (read-only SELECT only, LIMIT enforced)
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List

DB_PATH = Path(__file__).resolve().parents[1] / "db" / "sample.sqlite"

BLOCKED = re.compile(r"\b(drop|delete|update|insert|alter|create|attach|detach|pragma|vacuum|replace)\b", re.I)


def _normalize(sql: str) -> str:
    return " ".join(sql.strip().split())


def _ensure_safe_select(sql: str) -> str:
    sql_n = _normalize(sql)

    if not sql_n.lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    if ";" in sql_n:
        raise ValueError("Semicolons are not allowed.")

    if BLOCKED.search(sql_n):
        raise ValueError("Dangerous keyword detected.")

    # /// enforce a hard LIMIT 50 if missing
    if re.search(r"\blimit\b", sql_n, re.I) is None:
        sql_n = f"{sql_n} LIMIT 50"

    return sql_n


def get_schema_text(db_path: Path = DB_PATH) -> str:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in cur.fetchall()]

    lines: List[str] = []
    for t in tables:
        cur.execute(f"PRAGMA table_info({t});")
        cols = cur.fetchall()  # (cid, name, type, notnull, dflt_value, pk)
        col_str = ", ".join([f"{c[1]} {c[2]}" for c in cols])
        lines.append(f"{t}({col_str})")

    conn.close()
    return "\n".join(lines)


class SQLTool:
    name = "sql"
    description = "Execute read-only SELECT queries against local SQLite sample DB."
    input_schema = {
        "type": "object",
        "properties": {"sql": {"type": "string"}},
        "required": ["sql"],
    }

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        start = perf_counter()
        sql_raw = input.get("sql", "")
        sql = _ensure_safe_select(sql_raw)

        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute(sql)
        rows = cur.fetchall()

        cols = list(rows[0].keys()) if rows else []
        data = [dict(r) for r in rows]

        conn.close()

        elapsed_ms = int((perf_counter() - start) * 1000)
        return {
            "sql": sql,
            "columns": cols,
            "rows": data,
            "row_count": len(data),
            "elapsed_ms": elapsed_ms,
        }
