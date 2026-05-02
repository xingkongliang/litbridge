"""PDF/DOCX parsing, chunking, embedding, and numpy cosine retrieval."""
from __future__ import annotations

import json
import re
import math
import os
from dataclasses import dataclass, asdict
from pathlib import Path

import fitz
import numpy as np
from docx import Document

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384
TARGET_TOKENS = 500
MAX_TOKENS = 700
REF_HEADERS = ("references", "bibliography", "参考文献")


@dataclass
class Chunk:
    file: str
    label: str  # "related" or "unrelated" — for eval display
    page: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def _approx_tokens(s: str) -> int:
    return len(s) // 4 or 1


def _strip_references(pages: list[str]) -> list[str]:
    """Cut everything after the References / Bibliography header (case-insensitive line match)."""
    out = []
    for txt in pages:
        lines = txt.split("\n")
        keep = []
        cut = False
        for line in lines:
            stripped = line.strip().lower().rstrip(":")
            if stripped in REF_HEADERS:
                cut = True
                break
            keep.append(line)
        out.append("\n".join(keep))
        if cut:
            break
    return out


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_pdf(path: Path, label: str) -> list[Chunk]:
    """Parse a PDF, strip References tail, merge paragraphs into 400-700 token chunks."""
    doc = fitz.open(path)
    pages = [p.get_text() for p in doc]
    pages = _strip_references(pages)
    doc.close()

    chunks: list[Chunk] = []
    for page_idx, page_text in enumerate(pages, start=1):
        buf, buf_tok = "", 0
        for para in _split_paragraphs(page_text):
            tok = _approx_tokens(para)
            if buf and buf_tok + tok > MAX_TOKENS:
                chunks.append(Chunk(path.name, label, page_idx, buf.strip()))
                buf, buf_tok = "", 0
            buf = (buf + "\n\n" + para).strip()
            buf_tok += tok
            if buf_tok >= TARGET_TOKENS:
                chunks.append(Chunk(path.name, label, page_idx, buf.strip()))
                buf, buf_tok = "", 0
        if buf and buf_tok > 30:
            chunks.append(Chunk(path.name, label, page_idx, buf.strip()))
    return chunks


def parse_docx(path: Path) -> list[str]:
    """Return body paragraphs from a docx, stripping References block."""
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    body, refs_started = [], False
    for p in paragraphs:
        if re.match(r"^\s*\[?\d+\]", p) or p.lower().rstrip(":") in REF_HEADERS:
            refs_started = True
        if not refs_started:
            body.append(p)
    return body


def is_substantive(paragraph: str, min_chars: int = 150) -> bool:
    """Skip headers and chemistry equations; keep real prose paragraphs."""
    if len(paragraph) < min_chars:
        return False
    # Mostly symbols / formulas?
    alpha = sum(c.isalpha() for c in paragraph)
    return alpha / len(paragraph) > 0.5


def load_embedder():
    """Lazy import + cache-only load to avoid UI hangs from model downloads."""
    from sentence_transformers import SentenceTransformer

    allow_download = os.environ.get("LITBRIDGE_ALLOW_MODEL_DOWNLOAD") == "1"
    return SentenceTransformer(EMBED_MODEL, local_files_only=not allow_download)


def embed_texts(model, texts: list[str]) -> np.ndarray:
    """Batched local embedding, L2-normalized so retrieval can be a dot product."""
    arr = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return arr.astype(np.float32)


def save_index(index_dir: Path, chunks: list[Chunk], embeddings: np.ndarray) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / "chunks.json").write_text(
        json.dumps([c.to_dict() for c in chunks], ensure_ascii=False, indent=1)
    )
    np.save(index_dir / "embeddings.npy", embeddings)


def load_index(index_dir: Path) -> tuple[list[Chunk], np.ndarray]:
    chunk_dicts = json.loads((index_dir / "chunks.json").read_text())
    chunks = [Chunk(**c) for c in chunk_dicts]
    embeddings = np.load(index_dir / "embeddings.npy")
    return chunks, embeddings


def retrieve(
    query_embedding: np.ndarray,
    chunks: list[Chunk],
    embeddings: np.ndarray,
    k: int = 5,
) -> list[tuple[Chunk, float]]:
    """Cosine similarity top-k. Embeddings assumed L2-normalized; query normalized here."""
    q = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
    scores = embeddings @ q
    top = np.argsort(-scores)[:k]
    return [(chunks[i], float(scores[i])) for i in top]


def keyword_retrieve(query: str, chunks: list[Chunk], k: int = 5) -> list[tuple[Chunk, float]]:
    """Small dependency-free fallback when the local embedding model is unavailable."""
    terms = [
        t
        for t in re.findall(r"[a-zA-Z][a-zA-Z0-9]{2,}", query.lower())
        if t
        not in {
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "into",
            "does",
            "how",
            "role",
        }
    ]
    if not terms:
        return []

    query_terms = set(terms)
    scored: list[tuple[Chunk, float]] = []
    n_chunks = len(chunks)
    doc_freq = {
        term: sum(1 for c in chunks if term in c.text.lower()) or 1
        for term in query_terms
    }
    for chunk in chunks:
        text = chunk.text.lower()
        score = 0.0
        for term in query_terms:
            tf = text.count(term)
            if tf:
                score += (1.0 + math.log(tf)) * math.log((n_chunks + 1) / doc_freq[term])
        if score > 0:
            scored.append((chunk, score))

    scored.sort(key=lambda item: -item[1])
    if not scored:
        return []
    max_score = scored[0][1] or 1.0
    return [(c, s / max_score) for c, s in scored[:k]]
