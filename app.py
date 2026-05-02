"""LitBridge — Streamlit app: Smart Cite-Back + Topic Search."""
from __future__ import annotations

import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rag import (
    embed_texts,
    is_substantive,
    keyword_retrieve,
    load_embedder,
    load_index,
    parse_docx,
    retrieve,
)
from llm import MODEL, cite_back, topic_summary

load_dotenv()

ROOT = Path(__file__).resolve().parent
INDEX_DIR = ROOT / "data" / "index"
AI_AGENT_DIR = ROOT / "data" / "papers" / "AI-Agent"
SAMPLE_DOCX = AI_AGENT_DIR / "user-draft-llm-agents.docx"
TITLES_JSON = AI_AGENT_DIR / "titles.json"
LOGO_PATH = ROOT / "assets" / "logo.png"

st.set_page_config(
    page_title="LitBridge",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "📚",
    layout="wide",
)
if LOGO_PATH.exists():
    st.logo(str(LOGO_PATH), size="large")

CSS = """
<style>
.lb-chunk {
    padding: 10px 12px;
    margin: 6px 0;
    border-radius: 8px;
    font-size: 13px;
    line-height: 1.65;
    color: #475569;
    background: white;
    border: 1px solid #f1f5f9;
}
.lb-chunk.match {
    background: rgba(252, 211, 77, 0.28);
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-left: 4px solid #f59e0b;
    color: #78350f;
    font-weight: 500;
}
.lb-chunk-page {
    display: inline-block;
    font-weight: bold;
    color: #2563eb;
    font-size: 11px;
    margin-right: 6px;
    letter-spacing: 0.02em;
}
.lb-ai-card {
    background: linear-gradient(135deg, #eff6ff 0%, #eef2ff 100%);
    border: 1px solid #bfdbfe;
    border-left: 4px solid #3b82f6;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.lb-ai-title {
    font-size: 12px;
    font-weight: 700;
    color: #1e3a8a;
    margin-bottom: 8px;
    letter-spacing: 0.02em;
}
.lb-ai-reason {
    font-size: 12px;
    color: #475569;
    line-height: 1.55;
}
.lb-para {
    padding: 10px 14px;
    margin: 4px 0;
    border-radius: 8px;
    line-height: 1.75;
    font-size: 14px;
    color: #334155;
    border-left: 4px solid transparent;
}
.lb-para.active {
    background: #eff6ff;
    border-left-color: #3b82f6;
}
.lb-cite {
    color: #2563eb;
    font-weight: 700;
    margin-left: 2px;
    font-size: 11px;
}
.lb-suggest {
    display: inline-block;
    font-size: 10px;
    background: #ffedd5;
    color: #c2410c;
    padding: 2px 9px;
    border-radius: 999px;
    font-weight: 600;
    margin-left: 8px;
    vertical-align: middle;
}
.lb-done {
    display: inline-block;
    font-size: 10px;
    background: #d1fae5;
    color: #065f46;
    padding: 2px 9px;
    border-radius: 999px;
    font-weight: 600;
    margin-left: 8px;
    vertical-align: middle;
}
.lb-pane-title {
    font-weight: 700;
    font-size: 13px;
    color: #1e293b;
    margin: 0 0 8px 0;
    letter-spacing: 0.02em;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


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
def get_index():
    if not (INDEX_DIR / "embeddings.npy").exists():
        st.error(
            "Index not found. Run `python scripts/preindex.py` locally and commit "
            "`data/index/` to the repo."
        )
        st.stop()
    return load_index(INDEX_DIR)


@st.cache_resource
def get_embedder():
    return load_embedder()


@st.cache_resource
def get_titles() -> dict[str, dict]:
    """filename -> {title, authors, year}. Empty dict if titles.json absent."""
    if not TITLES_JSON.exists():
        return {}
    try:
        return json.loads(TITLES_JSON.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def display_title(filename: str) -> str:
    meta = TITLES.get(filename)
    return meta["title"] if meta and meta.get("title") else filename


def display_meta(filename: str) -> str:
    meta = TITLES.get(filename)
    if not meta:
        return ""
    parts = [meta.get("authors", ""), meta.get("year", "")]
    return " · ".join(p for p in parts if p)


def retrieve_for_text(query: str, k: int):
    try:
        embedder = get_embedder()
        q_emb = embed_texts(embedder, [query])[0]
        return retrieve(q_emb, chunks, embeddings, k=k), "semantic"
    except Exception as exc:
        st.warning(
            "Local embedding model is not cached, using keyword fallback. "
            "Run once with model download enabled before the demo for semantic search."
        )
        st.caption(f"Fallback reason: {type(exc).__name__}: {exc}")
        return keyword_retrieve(query, chunks, k=k), "keyword"


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", " ")
    )


# ─── Header ────────────────────────────────────────────────────────────────
hero_l, hero_r = st.columns([1, 9], gap="small", vertical_alignment="center")
if LOGO_PATH.exists():
    hero_l.image(str(LOGO_PATH), width=72)
with hero_r:
    st.title("LitBridge")
    st.caption(
        "Your literature library × your paper — AI finds the evidence for the paragraph "
        "you are writing now."
    )

chunks, embeddings = get_index()
chunk_idx_by_id = {id(c): i for i, c in enumerate(chunks)}
TITLES = get_titles()

LIBRARY: dict[str, dict] = defaultdict(lambda: {"chunk_ids": []})
for i, c in enumerate(chunks):
    LIBRARY[c.file]["chunk_ids"].append(i)

# Sort library by year (desc) then title — uses titles.json metadata when available.
_library_items = sorted(
    LIBRARY.items(),
    key=lambda kv: (
        -int(TITLES.get(kv[0], {}).get("year", "0") or 0),
        display_title(kv[0]).lower(),
    ),
)
LIBRARY = dict(_library_items)

n_papers = len(LIBRARY)

c1, c2, c3 = st.columns(3)
c1.metric("Papers in library", n_papers, help="Reference papers indexed and searchable in the demo corpus.")
c2.metric("Searchable segments", len(chunks), help="Section-aware chunks the retriever scores against your draft paragraph.")
c3.metric("Citation model", MODEL, help="Claude model that judges relevance and writes the inline citation marker.")

tab_cite, tab_topic = st.tabs(["✍️ Smart Cite-Back", "🔍 Topic Search"])

# ─── Smart Cite-Back ───────────────────────────────────────────────────────
with tab_cite:
    st.session_state.setdefault("analysis", None)
    st.session_state.setdefault("active_draft_id", None)
    st.session_state.setdefault("active_match_idx", 0)
    st.session_state.setdefault("manual_ref_file", None)

    if st.session_state.analysis is None:
        # ─ Input form ─
        st.subheader("Find citations for the draft paragraph you are writing")
        st.caption(
            "Start with the bundled sample to see LitBridge match draft paragraphs to "
            "evidence from a 13-paper LLM-agent library."
        )
        src = st.radio(
            "Input source",
            [f"Use sample (`{SAMPLE_DOCX.name}`)", "Upload .docx", "Paste text"],
            horizontal=True,
            key="cite_src",
        )
        body_paragraphs: list[str] = []
        draft_title = "Draft"
        if src.startswith("Use sample"):
            if SAMPLE_DOCX.exists():
                body_paragraphs = parse_docx(SAMPLE_DOCX)
                draft_title = SAMPLE_DOCX.name
            else:
                st.warning("Sample docx missing.")
        elif src == "Upload .docx":
            up = st.file_uploader("Upload draft", type=["docx"], key="cite_up")
            if up:
                with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                    tmp.write(up.getbuffer())
                    body_paragraphs = parse_docx(Path(tmp.name))
                    draft_title = up.name
        else:
            txt = st.text_area("Paste paragraphs (separate with blank lines)", height=200)
            if txt.strip():
                body_paragraphs = [p.strip() for p in txt.split("\n\n") if p.strip()]
                draft_title = "Pasted Draft"

        targets = [p for p in body_paragraphs if is_substantive(p)]
        st.caption(
            f"Total paragraphs: {len(body_paragraphs)} · "
            f"citation-ready paragraphs: **{len(targets)}** "
            f"(short headings, equations, and references skipped)"
        )

        default_max_n = min(4, len(targets)) if targets else 0
        max_n = default_max_n
        k_ret = 3
        if targets:
            with st.expander("Advanced demo settings"):
                max_n = st.slider(
                    "Paragraphs to analyze",
                    1,
                    len(targets),
                    default_max_n,
                    help="Default keeps the demo fast while showing multiple citation matches.",
                )
                k_ret = st.slider(
                    "Citation candidates per paragraph",
                    1,
                    5,
                    3,
                    help="Higher values show more alternatives but take longer to score.",
                )
        else:
            st.info("No citation-ready paragraphs found. Upload or paste longer prose paragraphs.")

        if src.startswith("Use sample"):
            analyze_label = "🚀 Analyze sample draft"
        elif src == "Upload .docx":
            analyze_label = "🚀 Analyze uploaded draft"
        else:
            analyze_label = "🚀 Analyze pasted text"

        if st.button(analyze_label, type="primary", disabled=not targets):
            anth_key = _secret("ANTHROPIC_API_KEY")
            if not anth_key:
                st.error(
                    "Claude API key is missing, so the live citation scoring cannot run. "
                    "Set `ANTHROPIC_API_KEY` in Streamlit secrets or `.env`."
                )
                st.stop()

            paragraphs_data: list[dict] = []
            progress = st.progress(0.0, text="Analyzing…")
            try:
                for i, text in enumerate(targets[:max_n], 1):
                    progress.progress(i / max_n, text=f"Paragraph {i}/{max_n}")
                    hits, _mode = retrieve_for_text(text, k=k_ret * 2)
                    # Dedup by file (one match per paper, best-scoring)
                    seen, dedup = set(), []
                    for c, s in hits:
                        if c.file in seen:
                            continue
                        seen.add(c.file)
                        dedup.append((c, s))
                        if len(dedup) >= k_ret:
                            break
                    verdicts = cite_back(anth_key, text, dedup)
                    # Map verdict back to source chunk via (file, page)
                    key_to_chunk = {(c.file, c.page): c for c, _ in dedup}
                    matches = []
                    for v in verdicts[:k_ret]:
                        src_chunk = key_to_chunk.get((v.file, v.page))
                        if src_chunk is None:
                            continue
                        cid = chunk_idx_by_id[id(src_chunk)]
                        matches.append({
                            "chunk_id": cid,
                            "file": v.file,
                            "page": v.page,
                            "score": float(v.relevance),
                            "reason": v.reason,
                        })
                    paragraphs_data.append({
                        "id": f"d{i}",
                        "text": text,
                        "matches": matches,
                        "citations": [],
                    })
            except Exception as exc:
                progress.empty()
                st.error(f"Claude analysis failed via `{MODEL}`: {type(exc).__name__}: {exc}")
                st.stop()
            # Carry remaining substantive paragraphs without analysis
            for j, text in enumerate(targets[max_n:], max_n + 1):
                paragraphs_data.append({
                    "id": f"d{j}",
                    "text": text,
                    "matches": [],
                    "citations": [],
                })
            progress.empty()

            st.session_state.analysis = {"title": draft_title, "paragraphs": paragraphs_data}
            # Auto-activate first paragraph that has matches
            for p in paragraphs_data:
                if p["matches"]:
                    st.session_state.active_draft_id = p["id"]
                    break
            st.session_state.active_match_idx = 0
            st.session_state.manual_ref_file = None
            st.rerun()

    else:
        # ─ Workspace ─
        analysis = st.session_state.analysis
        head_l, head_r = st.columns([4, 1])
        head_l.caption(
            f"📝 **{analysis['title']}** · {len(analysis['paragraphs'])} paragraphs · "
            "click a draft paragraph to inspect its matched source"
        )
        if head_r.button("🔄 New analysis", use_container_width=True, key="reset"):
            st.session_state.analysis = None
            st.session_state.active_draft_id = None
            st.session_state.active_match_idx = 0
            st.session_state.manual_ref_file = None
            st.rerun()

        active_para = next(
            (p for p in analysis["paragraphs"] if p["id"] == st.session_state.active_draft_id),
            None,
        )
        active_match = None
        if active_para and active_para["matches"]:
            idx = min(st.session_state.active_match_idx, len(active_para["matches"]) - 1)
            active_match = active_para["matches"][idx]

        manual = st.session_state.manual_ref_file
        current_ref_file = (
            manual
            or (active_match["file"] if active_match else None)
            or next(iter(LIBRARY))
        )
        active_chunk_id = (
            active_match["chunk_id"]
            if (active_match and not manual and current_ref_file == active_match["file"])
            else None
        )

        col_lib, col_ref, col_draft = st.columns([22, 33, 45])

        # ─── Pane 1: Library ───
        with col_lib:
            st.markdown('<div class="lb-pane-title">📚 Library</div>', unsafe_allow_html=True)
            for fname, info in LIBRARY.items():
                is_active = current_ref_file == fname
                title = display_title(fname)
                meta = display_meta(fname)
                short = title if len(title) <= 60 else title[:57] + "…"
                btn_label = f"{short}"
                if meta:
                    btn_label = f"{short}\n_{meta} · {len(info['chunk_ids'])} chunks_"
                else:
                    btn_label = f"{short} · {len(info['chunk_ids'])}c"
                if st.button(
                    btn_label,
                    key=f"lib-{fname}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.manual_ref_file = fname
                    st.rerun()

        # ─── Pane 2: Reference Reader ───
        with col_ref:
            info = LIBRARY[current_ref_file]
            title = display_title(current_ref_file)
            meta = display_meta(current_ref_file)
            st.markdown(
                f'<div class="lb-pane-title">📖 {html_escape(title)}</div>',
                unsafe_allow_html=True,
            )
            caption_bits = []
            if meta:
                caption_bits.append(meta)
            caption_bits.append(f"{len(info['chunk_ids'])} chunks")
            caption_bits.append(f"`{current_ref_file}`")
            st.caption(" · ".join(caption_bits))

            if not manual and active_match:
                pct = int(round(active_match["score"] * 100))
                st.markdown(
                    f"""
<div class="lb-ai-card">
  <div class="lb-ai-title">✨ Citation evidence · relevance {pct}%</div>
  <div class="lb-ai-reason"><b>Why:</b> {html_escape(active_match['reason'] or '(no reason)')}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

                # Multi-match switcher
                if len(active_para["matches"]) > 1:
                    sw_cols = st.columns(len(active_para["matches"]))
                    for j, m in enumerate(active_para["matches"]):
                        label = f"#{j + 1} · {int(round(m['score'] * 100))}%"
                        if sw_cols[j].button(
                            label,
                            key=f"sw-{active_para['id']}-{j}",
                            type="primary" if j == st.session_state.active_match_idx else "secondary",
                            use_container_width=True,
                        ):
                            st.session_state.active_match_idx = j
                            st.session_state.manual_ref_file = None
                            st.rerun()

                already_cited = active_match["chunk_id"] in active_para["citations"]
                if already_cited:
                    st.success("✅ Citation inserted into the paragraph")
                else:
                    if st.button(
                        "➡️  Insert this citation",
                        type="primary",
                        use_container_width=True,
                        key="insert-cite",
                    ):
                        active_para["citations"].append(active_match["chunk_id"])
                        st.rerun()
            elif manual:
                st.caption("📌 Browsing library manually — click a draft paragraph to resume citation matches")
            else:
                st.caption("Click any draft paragraph to see citation evidence")

            st.markdown("---")
            for cid in info["chunk_ids"]:
                c = chunks[cid]
                is_match = cid == active_chunk_id
                cls = "lb-chunk match" if is_match else "lb-chunk"
                prefix = "📍 " if is_match else ""
                trimmed = c.text[:600]
                ellipsis = "…" if len(c.text) > 600 else ""
                st.markdown(
                    f'<div class="{cls}">'
                    f'<span class="lb-chunk-page">p.{c.page}</span> '
                    f'{prefix}{html_escape(trimmed)}{ellipsis}</div>',
                    unsafe_allow_html=True,
                )

        # ─── Pane 3: Draft Editor ───
        with col_draft:
            st.markdown(
                f'<div class="lb-pane-title">📝 {html_escape(analysis["title"])}</div>',
                unsafe_allow_html=True,
            )
            for para in analysis["paragraphs"]:
                is_active = para["id"] == st.session_state.active_draft_id
                n_matches = len(para["matches"])
                n_cites = len(para["citations"])

                btn_col, text_col = st.columns([1, 22], gap="small")
                with btn_col:
                    if st.button(
                        "▸",
                        key=f"sel-{para['id']}",
                        help="Select this paragraph",
                        type="primary" if is_active else "secondary",
                    ):
                        if n_matches:
                            st.session_state.active_draft_id = para["id"]
                            st.session_state.active_match_idx = 0
                            st.session_state.manual_ref_file = None
                            st.rerun()
                        else:
                            st.session_state.active_draft_id = para["id"]
                            st.session_state.manual_ref_file = None
                            st.rerun()
                with text_col:
                    text_html = html_escape(para["text"])
                    cite_sup = ""
                    if n_cites > 0:
                        cite_sup = (
                            " <sup class='lb-cite'>"
                            + "".join(f"[{i + 1}]" for i in range(n_cites))
                            + "</sup>"
                        )
                    badge = ""
                    if n_matches > 0 and n_cites < n_matches:
                        badge = f' <span class="lb-suggest">✨ {n_matches} suggestion{"s" if n_matches > 1 else ""}</span>'
                    elif n_matches > 0 and n_cites >= n_matches:
                        badge = ' <span class="lb-done">✅ all cited</span>'
                    cls = "lb-para active" if is_active else "lb-para"
                    st.markdown(
                        f'<div class="{cls}">{text_html}{cite_sup}{badge}</div>',
                        unsafe_allow_html=True,
                    )

# ─── Topic Search ──────────────────────────────────────────────────────────
with tab_topic:
    st.subheader("Ask a topic question across the paper library")
    samples = [
        "How does chain-of-thought prompting improve reasoning in LLMs?",
        "What role does RLHF play in aligning language models with human intent?",
        "How do generative agents simulate believable human-like behavior?",
        "Embodied LLM agents: how do they recover from low-level execution failures?",
    ]
    chosen = st.selectbox("Sample topics", samples, key="topic_sample")
    topic = st.text_input(
        "Topic / research question",
        value=chosen,
        max_chars=200,
        placeholder="e.g. how does chain-of-thought prompting improve reasoning?",
    )
    with st.expander("Advanced search settings"):
        k_topic = st.slider("Sources to retrieve", 3, 10, 5, key="topic_k")
    if st.button("🔍 Search & summarize", type="primary", disabled=not topic.strip()):
        anth_key = _secret("ANTHROPIC_API_KEY")
        if not anth_key:
            st.error(
                "Claude API key is missing, so the live summary cannot run. "
                "Set `ANTHROPIC_API_KEY` in Streamlit secrets or `.env`."
            )
            st.stop()
        with st.spinner("Retrieving sources…"):
            hits, mode = retrieve_for_text(topic, k=k_topic)
        try:
            with st.spinner("Synthesizing summary with Claude…"):
                summary = topic_summary(anth_key, topic, hits)
        except Exception as exc:
            st.error(f"Claude summary failed via `{MODEL}`: {type(exc).__name__}: {exc}")
            st.stop()
        st.markdown("### 📝 Summary")
        st.markdown(summary)
        st.markdown("### 📎 Sources")
        st.caption(f"Retrieval mode: {mode}")
        for c, score in hits:
            with st.container(border=True):
                title = display_title(c.file)
                meta = display_meta(c.file)
                head = f"**{title}** · p.{c.page} · score `{score:.3f}`"
                if meta:
                    head = f"**{title}** · _{meta}_ · p.{c.page} · score `{score:.3f}`"
                st.markdown(head)
                st.markdown(f"> {c.text[:500]}{'…' if len(c.text) > 500 else ''}")
