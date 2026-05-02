# LitBridge — Hackathon Execution Plan

> Date: 2026-05-02 · ANU AI Buildathon (8h, ~6.5h remaining)
> Related: `12-research-ai-literature-manager.md` (original brainstorm; this doc takes precedence)

---

## 1. Product

**One-liner**: your literature library × your draft / Topic, AI connects them.

- **A. Smart Cite-Back** (highlight): paste a draft → top-3 citation suggestions per paragraph
- **B. Topic Search** (fallback): enter a Topic → multi-paper summary + source excerpts

**Every result must include**: filename · page number · source excerpt · relevance. This is the lifeline of trust for AI suggestions.

---

## 2. Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Streamlit |
| Deployment | Streamlit Community Cloud |
| PDF | PyMuPDF (`fitz`) |
| Chunking | merge paragraphs to 400–700 tokens; truncate when `References` / `Bibliography` is detected (minimal version, no fancy regex) |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` (384-dim, local). **Empirically the Voyage free tier is rate-limited to 3 RPM / 10K TPM**, every demo query waited ~20s — unusable; switching back to local removes the limit entirely |
| Vector DB | ChromaDB in-memory client |
| LLM | Claude Haiku 4.5 (single model; keep a constant ready to switch to Sonnet 4.6) |

`requirements.txt`: `streamlit / PyMuPDF / chromadb / anthropic / voyageai / python-dotenv`

---

## 3. Architecture

```
app.py        # Streamlit UI + Feature A/B entry points
rag.py        # parsing + chunking + embed + Chroma + retrieve
llm.py        # Claude wrapper + JSON-parsing fallback

data/
  pdfs/         # 5-10 demo PDFs (arXiv / Open Access)
  sample_draft.md
  index/        # locally precomputed chunks.json + embeddings.npy (deploy safety net, see §5)
```

A and B share the same `rag.retrieve(query, k)`. Claude only summarises and judges.

---

## 4. Timeline (6.5h)

| Slot | Content |
|------|---------|
| **0:00 – 0:15** | Smoke deploy: minimal skeleton + Secrets + public URL. **If 15 min isn't enough, switch to HF Spaces or a local tunnel** |
| **0:15 – 1:30** | rag.py: PDF → chunks → Voyage embed → Chroma; precompute `data/index/` cache locally |
| **1:30 – 3:00** | **Feature B** (shortest end-to-end loop): topic → retrieve → Claude summary |
| **3:00 – 4:30** | **Feature A**: split draft into paragraphs → retrieve per paragraph → Claude top-3 ranking + JSON |
| **4:30 – 5:30** | Safety net + polish: sample button, input length cap, JSON-parsing fallback, network-failure messaging |
| **5:30 – 6:30** | Pitch + demo rehearsal + backup screen recording |

**Hard freeze: 4:30.**

### Ingestion fallback chain

1. Primary path fails → fall back to locally precomputed `chunks.json` + `embeddings.npy`, Cloud only loads
2. Still fails → drop embeddings, switch to `rank_bm25` keyword retrieval + Claude summary

---

## 5. Deployment checklist (Streamlit Community Cloud)

1. Public GitHub repo, `app.py` at root
2. `requirements.txt` at root, `runtime.txt` says `python-3.11`
3. Secrets configure `ANTHROPIC_API_KEY` + `VOYAGE_API_KEY`; code reads via `st.secrets[...]`
4. Commit demo PDFs + precomputed `data/index/` into the repo (**deploy safety net**: Cloud only loads on startup, doesn't re-embed, avoiding cold-start API / network failures)
5. Wrap `load_index()` with `@st.cache_resource` to avoid reloads on rerun
6. **Five minutes before the demo, open the URL to warm it up**

Resources: 1 GB RAM is enough (Voyage runs over API and doesn't take RAM).

---

## 6. Engineering must-do checklist

When writing code, don't skip any of these:

- PDF extraction: visually inspect demo PDFs in advance for text quality (two-column / formulas / scans break easily)
- Chunking: detect `References` / `Bibliography` / `参考文献` keywords at the tail to truncate
- Streamlit: wrap heavy objects with `@st.cache_resource`, file reads with `@st.cache_data`
- Claude: request JSON output + regex-extract `\{.*\}` + try/except fallback
- Voyage: embed in batches; retry Anthropic calls
- Secrets: always go through `st.secrets`; don't print, don't commit

---

## 7. Demo path

```
1. Judges open the public URL → home page: "LitBridge" + "N papers loaded" + sample button
2. Feature B: click a sample topic → 3-5 results (filename · page · excerpt · relevance)
3. Feature A: click sample draft → paragraph-level top-3 citation suggestions
4. Closing one-liner
```

Lock this down early to avoid chaos in the last 30 minutes.

---

## 8. Out of scope

- ❌ Unit tests / abstraction layers / LangChain
- ❌ Vercel deploy (incompatible with Streamlit's long-lived connections)
- ❌ Local sentence-transformers (Voyage has better quality + saves RAM)
- ❌ Section-aware chunking / complex References regex
- ❌ One-click insert / drag-and-drop editor / markdown export
- ❌ Committing paid / copyrighted papers (public repo = public distribution)
- ❌ Prompt caching / two-tier model routing (hackathon ROI < debugging cost)

**Must keep**: every recommendation result includes **filename + page number + source excerpt**.
