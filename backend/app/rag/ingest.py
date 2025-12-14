from pathlib import Path
from pypdf import PdfReader

def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def read_pdf_file(path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(path))
    pages: list[tuple[int, str]] = []
    for idx, page in enumerate(reader.pages):
        txt = page.extract_text() or ""
        pages.append((idx + 1, txt))
    return pages
