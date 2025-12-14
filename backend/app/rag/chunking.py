from dataclasses import dataclass

@dataclass
class Chunk:
    text: str
    chunk_id: str
    source: str
    page: int | None = None

def chunk_text(text: str, source: str, page: int | None = None, chunk_size: int = 900, overlap: int = 150) -> list[Chunk]:
    text = (text or "").strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    i = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        piece = text[start:end].strip()
        if piece:
            cid = f"{source}#c{i}"
            chunks.append(Chunk(text=piece, chunk_id=cid, source=source, page=page))
            i += 1

        if end == len(text):
            break
        start = max(0, end - overlap)

    return chunks
