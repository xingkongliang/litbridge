"""LitBridge — Streamlit app: Smart Cite-Back + Topic Search."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
import voyageai
from dotenv import load_dotenv

from rag import (
    Chunk,
    embed_voyage,
    is_substantive,
    load_index,
    parse_docx,
    retrieve,
)
from llm import cite_back, topic_summary

load_dotenv()

ROOT = Path(__file__).resolve().parent
INDEX_DIR = ROOT / "data" / "index"
SAMPLE_DOCX = ROOT / "data" / "papers" / "user-test-paper.docx"

st.set_page_config(page_title="LitBridge", page_icon="📚", layout="wide")


def _secret(name: str) -> str:
    """Streamlit Cloud secrets first, then env var (.env / shell)."""
    try:
        v = st.secrets.get(name)
        if v:
            return v
    except (FileNotFoundError, AttributeError):
        pass
    return os.environ.get(name, "")


@st.cache_resource
def get_index() -> tuple[list[Chunk], np.ndarray]:
    if not (INDEX_DIR / "embeddings.npy").exists():
        st.error(
            "Index not found. Run `python scripts/preindex.py` locally and commit "
            "`data/index/` to the repo."
        )
        st.stop()
    return load_index(INDEX_DIR)


@st.cache_resource
def get_voyage() -> voyageai.Client:
    key = _secret("VOYAGE_API_KEY")
    if not key:
        st.error("VOYAGE_API_KEY missing — set it in Streamlit Cloud Secrets.")
        st.stop()
    return voyageai.Client(api_key=key)


def _label_badge(label: str) -> str:
    return "🟢 related" if label == "related" else "🟡 unrelated"


def render_hits(hits, *, show_score: bool = True) -> None:
    for c, score in hits:
        with st.container(border=True):
            head = f"**{c.file}** · p.{c.page} · {_label_badge(c.label)}"
            if show_score:
                head += f" · score `{score:.3f}`"
            st.markdown(head)
            st.markdown(f"> {c.text[:500]}{'…' if len(c.text) > 500 else ''}")


def render_verdicts(verdicts) -> None:
    for v in verdicts:
        with st.container(border=True):
            label = "🟢" if "unrelated" not in v.file.lower() else ""  # cosmetic
            st.markdown(
                f"**{v.file}** · p.{v.page} · relevance `{v.relevance:.2f}` {label}"
            )
            if v.reason:
                st.caption(v.reason)
            st.markdown(f"> {v.snippet}{'…' if len(v.snippet) >= 300 else ''}")


# ─── Header ────────────────────────────────────────────────────────────────
st.title("📚 LitBridge")
st.caption("Your literature library × your paper — AI connects them.")

chunks, embeddings = get_index()
n_papers = len({c.file for c in chunks})
n_related = len({c.file for c in chunks if c.label == "related"})
n_unrelated = len({c.file for c in chunks if c.label == "unrelated"})

c1, c2, c3, c4 = st.columns(4)
c1.metric("Papers loaded", n_papers)
c2.metric("Chunks indexed", len(chunks))
c3.metric("🟢 Related", n_related)
c4.metric("🟡 Unrelated (eval)", n_unrelated)
st.caption(
    "The corpus contains both **related** and **unrelated** papers from the same broad field. "
    "A good retriever should preferentially surface 🟢 related ones."
)

tab_cite, tab_topic = st.tabs(["✍️ Smart Cite-Back", "🔍 Topic Search"])

# ─── Smart Cite-Back ───────────────────────────────────────────────────────
with tab_cite:
    st.subheader("Paragraph-by-paragraph citation suggestions")

    src = st.radio(
        "Input source",
        ["Use sample (`user-test-paper.docx`)", "Upload .docx", "Paste text"],
        horizontal=True,
        key="cite_src",
    )

    body_paragraphs: list[str] = []
    if src.startswith("Use sample"):
        if SAMPLE_DOCX.exists():
            body_paragraphs = parse_docx(SAMPLE_DOCX)
        else:
            st.warning("Sample docx missing.")
    elif src == "Upload .docx":
        up = st.file_uploader("Upload draft", type=["docx"], key="cite_up")
        if up:
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp.write(up.getbuffer())
                body_paragraphs = parse_docx(Path(tmp.name))
    else:
        txt = st.text_area("Paste paragraphs (separate with blank lines)", height=200)
        if txt.strip():
            body_paragraphs = [p.strip() for p in txt.split("\n\n") if p.strip()]

    targets = [p for p in body_paragraphs if is_substantive(p)]
    st.caption(
        f"Total paragraphs: {len(body_paragraphs)} · "
        f"substantive (≥150 chars, prose): **{len(targets)}** "
        f"(headers / equations / references stripped)"
    )

    max_n = st.slider("How many paragraphs to analyze", 1, max(1, len(targets)), min(4, len(targets)) if targets else 1)
    k = st.slider("Top-K candidates per paragraph", 1, 5, 3)

    if st.button("🚀 Run Cite-Back", type="primary", disabled=not targets):
        anth_key = _secret("ANTHROPIC_API_KEY")
        if not anth_key:
            st.error("ANTHROPIC_API_KEY missing.")
            st.stop()
        client = get_voyage()
        progress = st.progress(0.0, text="Working…")
        for i, para in enumerate(targets[:max_n], 1):
            progress.progress(i / max_n, text=f"Paragraph {i}/{max_n}")
            with st.expander(f"Paragraph {i} ({len(para)} chars)", expanded=True):
                st.markdown(f"> {para[:400]}{'…' if len(para) > 400 else ''}")
                q_emb = embed_voyage(client, [para], "query")[0]
                hits = retrieve(q_emb, chunks, embeddings, k=k * 2)
                # de-dup by file, keep top per file
                seen, dedup = set(), []
                for c, s in hits:
                    if c.file in seen:
                        continue
                    seen.add(c.file)
                    dedup.append((c, s))
                    if len(dedup) >= k:
                        break
                verdicts = cite_back(anth_key, para, dedup)
                if verdicts:
                    render_verdicts(verdicts[:k])
                    related = sum(1 for v in verdicts[:k] if "unrelated" not in v.file.lower())
                    st.caption(f"🟢 retrieval signal: {related}/{k} candidates from related-papers")
                else:
                    st.warning("No candidates returned.")
        progress.empty()

# ─── Topic Search ──────────────────────────────────────────────────────────
with tab_topic:
    st.subheader("Topic → multi-paper summary")
    samples = [
        "How does CsBr incorporation affect phase segregation in wide-bandgap perovskites?",
        "Role of Cs4PbBr6 nanocrystals in perovskite crystallization",
        "Halide engineering strategies for stable wide-bandgap perovskite solar cells",
    ]
    chosen = st.selectbox("Sample topics", ["—"] + samples, key="topic_sample")
    topic = st.text_input(
        "Topic / research question",
        value=chosen if chosen != "—" else "",
        max_chars=200,
        placeholder="e.g. role of Cs4PbBr6 nanocrystals in perovskite crystallization",
    )
    k = st.slider("Top-K sources", 3, 10, 5, key="topic_k")
    if st.button("🔍 Search & summarize", type="primary", disabled=not topic.strip()):
        anth_key = _secret("ANTHROPIC_API_KEY")
        if not anth_key:
            st.error("ANTHROPIC_API_KEY missing.")
            st.stop()
        client = get_voyage()
        with st.spinner("Embedding query…"):
            q_emb = embed_voyage(client, [topic], "query")[0]
        hits = retrieve(q_emb, chunks, embeddings, k=k)
        with st.spinner("Synthesizing summary with Claude…"):
            summary = topic_summary(anth_key, topic, hits)
        st.markdown("### 📝 Summary")
        st.markdown(summary)
        st.markdown("### 📎 Sources")
        render_hits(hits)
        related = sum(1 for c, _ in hits if c.label == "related")
        st.caption(f"🟢 retrieval precision: {related}/{k} from related-papers")
