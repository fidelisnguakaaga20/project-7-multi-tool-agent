import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional


_DB_DIR = Path(__file__).resolve().parent.parent / "db"
_DB_DIR.mkdir(parents=True, exist_ok=True)

_MEM_DB = _DB_DIR / "agent_memory.sqlite"


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(_MEM_DB))
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            state_json TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
    con.commit()
    return con


def get_state(conversation_id: str) -> Dict[str, Any]:
    """
    Returns state dict. If missing, returns default empty state.
    """
    if not conversation_id:
        return {}

    con = _conn()
    try:
        cur = con.execute(
            "SELECT state_json FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = cur.fetchone()
        if not row:
            return {}
        return json.loads(row[0] or "{}")
    finally:
        con.close()


def save_state(conversation_id: str, state: Dict[str, Any]) -> None:
    if not conversation_id:
        return

    now = int(time.time())
    payload = json.dumps(state or {}, ensure_ascii=False)

    con = _conn()
    try:
        con.execute(
            """
            INSERT INTO conversations (conversation_id, state_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET
              state_json = excluded.state_json,
              updated_at = excluded.updated_at
            """,
            (conversation_id, payload, now),
        )
        con.commit()
    finally:
        con.close()


def update_state(conversation_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge patch into existing state and persist.
    """
    state = get_state(conversation_id)
    state.update(patch or {})
    save_state(conversation_id, state)
    return state


def extract_preferences_from_user_message(message: str) -> Dict[str, Any]:
    """
    Detect user preferences/goals and return a patch for memory.
    """
    msg = (message or "").lower()

    patch: Dict[str, Any] = {}

    # /// Tool preference: docs first / source of truth
    if "use my docs as source of truth" in msg or "docs as source of truth" in msg:
        patch["prefer_rag_first"] = True
        patch["docs_source_of_truth"] = True

    if "prefer docs first" in msg or "docs first" in msg:
        patch["prefer_rag_first"] = True

    if "don't use my docs" in msg or "do not use my docs" in msg:
        patch["prefer_rag_first"] = False
        patch["docs_source_of_truth"] = False

    # /// Store last goal (simple)
    if msg.startswith("my goal is") or "my goal:" in msg:
        patch["last_goal"] = message.strip()

    return patch


def update_retrieved_sources(conversation_id: str, sources: list[str]) -> None:
    """
    Save last retrieved sources (for Stage 8).
    """
    if not conversation_id:
        return

    state = get_state(conversation_id)
    state["last_sources"] = sources[:20]  # cap
    save_state(conversation_id, state)
