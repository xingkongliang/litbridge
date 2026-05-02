"""Pre-index all PDFs in data/papers/{related,unrelated}-papers/ into data/index/.
Run once locally before deploy. Output (chunks.json + embeddings.npy) is committed
to the repo so Streamlit Cloud can load instantly without re-embedding.

Usage:
    conda run -n llm python scripts/preindex.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag import Chunk, chunk_pdf, embed_texts, load_embedder, save_index  # noqa: E402

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
PAPERS_DIR = ROOT / "data" / "papers"
INDEX_DIR = ROOT / "data" / "index"


def main() -> None:
    sources = [
        (PAPERS_DIR / "related-papers", "related"),
        (PAPERS_DIR / "unrelated-papers", "unrelated"),
    ]

    all_chunks: list[Chunk] = []
    for folder, label in sources:
        if not folder.exists():
            print(f"  [skip] {folder} missing")
            continue
        pdfs = sorted(folder.glob("*.pdf"))
        print(f"[{label}] {len(pdfs)} PDFs")
        for i, pdf in enumerate(pdfs, 1):
            try:
                chunks = chunk_pdf(pdf, label)
                all_chunks.extend(chunks)
                print(f"  ({i}/{len(pdfs)}) {pdf.name} -> {len(chunks)} chunks")
            except Exception as e:
                print(f"  [err] {pdf.name}: {e}")

    print(f"\nTotal chunks: {len(all_chunks)}")
    if not all_chunks:
        sys.exit("No chunks produced.")

    print("Loading sentence-transformers model (first run downloads ~80MB)...")
    model = load_embedder()
    print(f"Embedding {len(all_chunks)} chunks (already L2-normalized)...")
    t0 = time.time()
    embeddings = embed_texts(model, [c.text for c in all_chunks])
    print(f"  done in {time.time() - t0:.1f}s, shape={embeddings.shape}")

    save_index(INDEX_DIR, all_chunks, embeddings)
    print(f"Saved to {INDEX_DIR}")


if __name__ == "__main__":
    main()
