import os
from pathlib import Path

# /// IMPORTANT: Disable Chroma telemetry BEFORE importing chromadb
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")  # /// Chroma checks this
os.environ.setdefault("CHROMA_TELEMETRY", "0")          # /// extra safety (varies by version)
os.environ.setdefault("CHROMA_ANONYMIZED_TELEMETRY", "0")

import chromadb  # noqa: E402
from chromadb.config import Settings  # noqa: E402


_DB_DIR = Path(__file__).resolve().parent.parent / "db"
_CHROMA_DIR = _DB_DIR / "chroma"


_client = None
_collection = None


def get_chroma_client():
    global _client
    if _client is not None:
        return _client

    _CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    # /// Persist locally, telemetry off
    _client = chromadb.PersistentClient(
        path=str(_CHROMA_DIR),
        settings=Settings(
            anonymized_telemetry=False,
        ),
    )
    return _client


def get_chroma_collection(name: str = "docs"):
    global _collection
    if _collection is not None:
        return _collection

    client = get_chroma_client()
    _collection = client.get_or_create_collection(name=name)
    return _collection
