"""Pre-index AI-Agent PDFs into data/index/.
Run once locally before deploy. Output (chunks.json + embeddings.npy) is committed
to the repo so Streamlit Cloud can load instantly without re-embedding.

Sources:
  - data/papers/AI-Agent/reference/*.pdf       (the user's literature library)
  - data/papers/AI-Agent/Generative_Agents_*.pdf (also a reference candidate)

Usage:
    conda run -n llm python scripts/preindex.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag import Chunk, chunk_pdf, embed_texts, load_embedder, save_index  # noqa: E402

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
PAPERS_DIR = ROOT / "data" / "papers"
AI_AGENT_DIR = PAPERS_DIR / "AI-Agent"
INDEX_DIR = ROOT / "data" / "index"


def main() -> None:
    ref_dir = AI_AGENT_DIR / "reference"
    extra_pdf = AI_AGENT_DIR / "Generative_Agents_Interactive_Simulacra_of_Human_Behavior.pdf"

    pdfs: list[Path] = []
    if ref_dir.exists():
        pdfs.extend(sorted(ref_dir.glob("*.pdf")))
    if extra_pdf.exists():
        pdfs.append(extra_pdf)

    if not pdfs:
        sys.exit(f"No PDFs found under {AI_AGENT_DIR}")

    print(f"[ai-agent] {len(pdfs)} PDFs")
    all_chunks: list[Chunk] = []
    for i, pdf in enumerate(pdfs, 1):
        try:
            chunks = chunk_pdf(pdf, "related")
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
