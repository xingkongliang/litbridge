# AI Literature Manager — Research Notes

> Date: 2026-05-02
> Setting: ANU AI Buildathon 2026.05
> Core need: upload your own literature library → intelligently insert citations into your draft / Topic → literature summary

---

## Requirements

### Feature 1: Library → existing draft (smart citation insertion)

The user has a draft they're writing plus a collection of papers (PDFs). The system analyses each paragraph of the draft, retrieves the most relevant excerpts from the library, and suggests where to insert citations. The user confirms.

### Feature 2: Library → new Topic (summary with evidence)

The user enters a research Topic or question. The system retrieves, reads, and summarises content from the existing library that supports that argument, helping the user quickly understand how the library covers the Topic.

### One-line summary

**Given a literature library and a goal (draft or Topic), the system finds the most relevant content for you and organises it.**

---

## 1. Competitive landscape

| Tool | Core capability | Differentiator |
|------|-----------------|----------------|
| **Sourcely** | Auto-find references + insert citations | Skewed toward undergrad essays, lacks depth |
| **Elicit** | Topic → literature search + summary | Strong on search, not on your own library |
| **Consensus** | Topic → multi-paper evidence aggregation | Only does search, doesn't manage your own library |
| **Scite** | Citation relationship analysis (support / contradict / mention) | Focused on citation networks, not writing assistance |
| **Anara** | Upload PDF → AI analysis + citation verification | Newest, multi-media, but paid |
| **Zotero** | Classic literature management + browser plugin | No AI capability, relies on plugin ecosystem |

**Wedge**: the market is missing a tool that does "you upload your own library → smart matching and insertion into your own draft". Existing tools either only search (Elicit / Consensus) or only manage (Zotero); none does the **your library × your draft → smart insertion** middle layer.

---

## 2. Core technical approach

### Overall architecture

Classic **RAG (Retrieval-Augmented Generation)**, customised for an academic setting.

### Recommended stack

- **Frontend**: Streamlit (fastest path to demo, full-stack Python, top hackathon choice)
- **PDF parsing**: `PyMuPDF` (text extraction) + `unstructured` (complex layout / tables)
- **Embedding**: OpenAI `text-embedding-3-small` (cheap, good quality) or `SPECTER2` (academic-specific, free)
- **Vector database**: ChromaDB or FAISS (local, zero config, sufficient for a hackathon)
- **LLM**: GPT-4o-mini (cheap and fast, good enough for matching and summarisation)
- **Chunking strategy**: chunk academic papers by section (Abstract, Method, Results, Conclusion); semantically more complete than fixed-token chunking

### Two pipelines

```
Pipeline A: literature library → vector index (precomputed, run once)
  PDF → text extraction → chunk by paragraph / section → embedding → store in ChromaDB

Pipeline B: user draft / Topic → retrieval + generation
  Draft paragraph → embedding → retrieve top-K relevant excerpts from ChromaDB
  → LLM scores match + generates citation suggestion → show options to the user
```

---

## 3. Reference open-source projects

1. **kotaemon** (https://github.com/Cinnamon/kotaemon) — open-source RAG document-chat tool, nice UI, supports multi-user and file management. Could fork for the frontend base and save time.
2. **scientific-paper-chat-rag** (https://github.com/StadynR/scientific-paper-chat-rag) — lightweight academic-paper RAG chat; code is simple and easy to follow, good architectural reference.
3. **research-assistant-rag** (https://github.com/aragit/research-assistant-rag) — fully local RAG research assistant; useful reference for the literature-processing pipeline.

---

## 4. Key APIs

- **Semantic Scholar API** (free): paper search, citation relationships, similar-paper recommendations, SPECTER2 embeddings. Works without an API key (with a key you get higher rate limits). Docs: https://api.semanticscholar.org/api-docs/
- **OpenAI API**: embeddings + GPT-4o-mini — the core depends on this.

---

## 5. 8-hour execution plan

| Phase | Time | Task |
|-------|------|------|
| 0–1h | Scaffolding | Streamlit skeleton + PDF upload + basic UI |
| 1–2.5h | Core A | PDF parsing → chunking → embedding → ChromaDB storage pipeline |
| 2.5–4.5h | Core B | Draft / Topic input → retrieval → match-score ranking → citation-suggestion display |
| 4.5–5.5h | Feature B | Topic → literature summary (second feature) |
| 5.5–6.5h | Polish | UI polish + mock data prep + error handling |
| 6.5–7.5h | Rehearsal | Demo script + pitch prep |

**Mock-data strategy**: prepare 5–10 papers in a single domain (e.g. NLP or medical) plus one half-finished draft so the demo has the shortest, clearest path to a wow moment.

---

## 6. Demo highlights

1. **Visualise the matching process**: highlight a draft paragraph → show matched excerpts + relevance scores on the right; user clicks to insert
2. **Before/after comparison**: show "manual citation hunting vs AI suggestions" time difference
3. **One-line pitch**: "Your literature library, your draft, AI connects them."
