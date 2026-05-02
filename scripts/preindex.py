"""Pre-index all PDFs in data/papers/{related,unrelated}-papers/ into data/index/.
Run once locally before deploy. Output (chunks.json + embeddings.npy) is committed
to the repo so Streamlit Cloud can load instantly without re-embedding.

Usage:
    conda run -n llm python scripts/preindex.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import voyageai
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag import Chunk, chunk_pdf, embed_voyage, save_index  # noqa: E402

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
PAPERS_DIR = ROOT / "data" / "papers"
INDEX_DIR = ROOT / "data" / "index"


def main() -> None:
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        sys.exit("VOYAGE_API_KEY not set (put in .env or export).")

    client = voyageai.Client(api_key=api_key)

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

    print("Embedding via Voyage voyage-context-3 ...")
    t0 = time.time()
    embeddings = embed_voyage(client, [c.text for c in all_chunks], "document")
    # Normalize once at index time so retrieval is just dot product
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / np.maximum(norms, 1e-9)
    print(f"  done in {time.time() - t0:.1f}s, shape={embeddings.shape}")

    save_index(INDEX_DIR, all_chunks, embeddings)
    print(f"Saved to {INDEX_DIR}")


if __name__ == "__main__":
    main()
