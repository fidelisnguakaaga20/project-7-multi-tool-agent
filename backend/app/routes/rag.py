import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel, Field

from app.rag.ingest import read_text_file, read_pdf_file
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_texts
from app.rag.store import get_chroma_collection

router = APIRouter()

UPLOAD_DIR = Path(os.path.join(os.path.dirname(__file__), "..", "uploads")).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(4, ge=1, le=10)

@router.post("/rag/index")
async def rag_index(files: list[UploadFile] = File(...)):
    col = get_chroma_collection()

    all_ids, all_docs, all_metas = [], [], []

    for f in files:
        filename = f.filename or "uploaded"
        save_path = UPLOAD_DIR / filename
        content = await f.read()
        save_path.write_bytes(content)

        ext = save_path.suffix.lower()

        if ext == ".pdf":
            pages = read_pdf_file(save_path)
            for page_num, page_text in pages:
                chunks = chunk_text(page_text, source=filename, page=page_num)
                for ch in chunks:
                    all_ids.append(ch.chunk_id)
                    all_docs.append(ch.text)
                    all_metas.append({"source": ch.source, "page": ch.page})
        else:
            text = read_text_file(save_path)
            chunks = chunk_text(text, source=filename, page=None)
            for ch in chunks:
                all_ids.append(ch.chunk_id)
                all_docs.append(ch.text)
                all_metas.append({"source": ch.source, "page": ch.page})

    if not all_docs:
        return {"ok": False, "message": "No text extracted from uploaded files."}

    # We control embeddings ourselves (no Chroma ONNX auto-download)
    embeddings = embed_texts(all_docs)
    col.upsert(ids=all_ids, documents=all_docs, metadatas=all_metas, embeddings=embeddings)

    return {"ok": True, "files_indexed": len(files), "chunks_added": len(all_docs)}

@router.post("/rag/query")
def rag_query(payload: RagQueryRequest):
    col = get_chroma_collection()

    # Prevent ONNX auto-embedding by supplying query embeddings ourselves
    q_emb = embed_texts([payload.query])[0]

    res = col.query(
        query_embeddings=[q_emb],
        n_results=payload.top_k,
        include=["documents", "metadatas", "distances"],  # ✅ valid in Chroma 0.5.x
    )

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    ids = res.get("ids", [[]])[0]  # ✅ ids are returned automatically (don’t include it)
    dists = res.get("distances", [[]])[0]

    out = []
    for doc, meta, cid, dist in zip(docs, metas, ids, dists):
        out.append(
            {
                "chunk_id": cid,
                "source": (meta or {}).get("source", "unknown"),
                "page": (meta or {}).get("page", None),
                "distance": dist,
                "text_preview": (doc[:220] + "...") if doc and len(doc) > 220 else doc,
            }
        )

    return {"matches": out}
