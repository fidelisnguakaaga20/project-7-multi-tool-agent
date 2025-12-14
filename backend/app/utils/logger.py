import time
import uuid
from typing import Any, Dict


def log_event(
    *,
    event: str,
    conversation_id: str | None,
    tool: str | None,
    status: str,
    latency_ms: int,
    meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "event": event,
        "conversation_id": conversation_id,
        "tool": tool,
        "status": status,
        "latency_ms": latency_ms,
        "meta": meta or {},
        "ts": int(time.time() * 1000),
    }
