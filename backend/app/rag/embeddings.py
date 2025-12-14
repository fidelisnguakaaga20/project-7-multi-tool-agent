import os
import math
import hashlib
from typing import List, Optional

# /// Make HuggingFace more tolerant on slow networks (applies before imports use it)
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_TIMEOUT", "60")  # /// was effectively ~10s for your run
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# /// Optional: force offline mode (set in your shell if needed)
# os.environ["HF_HUB_OFFLINE"] = "1"
# os.environ["TRANSFORMERS_OFFLINE"] = "1"

_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# /// Fallback: if HF download is blocked, you can use deterministic local hash embeddings
# Set EMBED_BACKEND=hash to force offline embeddings (works for demo; not semantic-quality).
_BACKEND = os.getenv("EMBED_BACKEND", "hf").strip().lower()  # hf | hash

# /// If you want to force cache-only usage (no network), set EMBED_LOCAL_ONLY=1
_LOCAL_ONLY = os.getenv("EMBED_LOCAL_ONLY", "0") == "1"


_st_model = None


def _hash_embed(text: str, dim: int = 384) -> List[float]:
    """
    Deterministic offline embedding:
    - NOT semantic
    - BUT stable vectors so Chroma pipeline works without internet
    """
    v = [0.0] * dim
    if not text:
        return v

    # chunk into tokens-ish
    parts = text.split()
    for p in parts[:2000]:
        h = hashlib.sha256(p.encode("utf-8")).digest()
        # spread bytes across vector
        for i in range(0, len(h), 2):
            idx = (h[i] << 8 | h[i + 1]) % dim
            v[idx] += 1.0

    # normalize
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def _load_sentence_transformer() -> Optional[object]:
    """
    Loads SentenceTransformer model.
    - If EMBED_LOCAL_ONLY=1, will never attempt network.
    - If loading fails (timeout / blocked), returns None.
    """
    global _st_model
    if _st_model is not None:
        return _st_model

    try:
        from sentence_transformers import SentenceTransformer

        # /// local_files_only prevents any network calls when True
        _st_model = SentenceTransformer(_MODEL_NAME, local_files_only=_LOCAL_ONLY)
        return _st_model
    except Exception:
        return None


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Returns embeddings for a list of texts.
    Primary: HuggingFace sentence-transformers (semantic)
    Fallback: deterministic hash vectors (offline)
    """
    texts = texts or []

    # /// If forced hash backend
    if _BACKEND == "hash":
        return [_hash_embed(t) for t in texts]

    # /// Try HF backend
    model = _load_sentence_transformer()
    if model is None:
        # /// fallback if HF blocked
        return [_hash_embed(t) for t in texts]

    # SentenceTransformer returns numpy arrays -> convert to list for JSON friendliness
    vecs = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return [v.tolist() for v in vecs]
