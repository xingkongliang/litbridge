# Stack comparison: current setup vs full Azure

> Date: 2026-05-02
> Context: LitBridge hackathon, 6.5h remaining; evaluating whether to swap PDF parsing and the vector store for Azure services
> Related: `15-hackathon-execution-plan.md` (final plan)

---

## 1. PDF parsing

| Dimension | PyMuPDF (current) | Azure Document Intelligence |
|-----------|-------------------|------------------------------|
| Install / config | `pip install` and you're done | Azure account + resource provision + API key + SDK, **~30–60 min** |
| Clean arXiv PDFs | 95% fine | Equally good |
| Complex tables / formulas | No structure | **Clearly stronger** (layout model returns structured JSON) |
| Scans / OCR | ❌ No support | ✅ Built-in OCR |
| Multi-column layout | Text order can break | Auto-restored to reading order |
| Parsing latency | <100ms / PDF (local) | **5–15s / PDF** (network round-trip) |
| Failure points | Local code only | API / network / rate limit / auth (4) |
| Free tier | Unlimited | 500 pages/month F0 tier (enough for a hackathon) |

---

## 2. Vector database

| Dimension | ChromaDB in-memory (current) | Azure AI Search |
|-----------|------------------------------|------------------|
| Install / config | Zero config | Resource provision + index schema + vector fields + indexer, **~30–60 min** |
| 5–10 PDFs / 100–500 chunks performance | Microsecond-scale cosine | Equally fast, plus a network round-trip |
| Persistence | None (need to commit `data/index/`) | ✅ Built-in |
| Hybrid retrieval (vector + keyword) | Have to implement yourself | ✅ Built-in |
| Semantic ranker | None | ✅ but **only on Basic and above** (~$75/month and up) |
| Free tier | Unlimited locally | F1 tier: 50MB storage / 3 indexes / no semantic ranker |
| Failure points | Local only | API / index sync / network (3) |

---

## 3. Total cost

| Metric | Current setup | Full Azure |
|--------|---------------|------------|
| Total setup time | 0 (ready to go) | **~2h (31% of remaining time)** |
| Network failure points | 1 | **7** (DI 4 + Search 3) |
| Risk from flaky on-site wifi | Only judge access | Hits every PDF parse + retrieval |
| Demo quality lift (at 5 arXiv-paper scale) | — | Judges can't tell the difference |

---

## 4. Decision matrix

| Scenario | Recommendation |
|----------|----------------|
| **No Azure sponsor bonus** (no "Best Use of Azure" prize) | Keep PyMuPDF + ChromaDB. Azure here is "doing the wrong thing the right way" |
| **Azure bonus exists** | **Hybrid**: Document Intelligence for parsing (real quality lift) + still ChromaDB in-memory (AI Search setup cost not worth it) |
| **Demo PDFs include scans / complex tables / formulas** | Even without an Azure bonus, **swap only Document Intelligence**; don't swap AI Search |

---

## 5. The two variables that decide Azure's value

Before swapping, you must answer:

1. **Does the ANU AI Buildathon have an Azure / Microsoft sponsor bonus?**
   - If a "Best Use of Azure" prize or Azure-as-main-sponsor exists, the bonus is product value itself and the cost calculation flips
2. **What's the quality of the demo PDFs?**
   - All clean LaTeX arXiv → PyMuPDF is enough
   - Includes scans / complex tables / multi-column / formulas → Document Intelligence has real value

These two variables decide everything. Don't switch before you know the answers.

---

## 6. Conclusion

**Default: stay on the current setup** (PyMuPDF + ChromaDB in-memory).

Only consider switching if **a sponsor bonus is confirmed** or **demo-PDF quality is complex**. Even then, only swap in Document Intelligence; AI Search is never worth it at hackathon scale.

Hackathon judges don't grade based on tech-stack brand — they grade based on how impressive the demo is. Every extra hour of setup is one less hour polishing the wow moments.
