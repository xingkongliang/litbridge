# LitBridge × Theme Brief — Fit Analysis

> Date: 2026-05-02
> Context: ANU AI Buildathon — Theme: Tool for Students

---

## Central-challenge fit

| Requirement | LitBridge |
|-------------|-----------|
| Help students solve a **real** academic problem | ✅ Finding citations while writing is a real pain point for every grad student |
| Not a generic chatbot | ✅ Two well-defined workflows (citation suggestions for a draft / Topic literature lookup) |
| Clear workflow | ✅ Upload PDFs → system indexes → input draft / Topic → get suggestions |
| Demonstrable value | ✅ Whole flow from draft to citation suggestion visible within 90 seconds |

---

## Focus-area mapping

**Target direction: The Struggling Learner** — help students understand difficult course content.

| Expectation | LitBridge | Fit |
|-------------|-----------|-----|
| Diagnose what the student doesn't understand | LitBridge doesn't diagnose "where the student is stuck"; it helps them find supporting literature | ⚠️ Weak |
| Explain concepts via examples / steps / analogies | Not done. LitBridge doesn't explain concepts themselves | ❌ |
| Include practice questions and feedback | Not done | ❌ |
| Encourage active learning rather than giving answers | Suggests citations so the student goes back to the source, not auto-writes the paragraph | ✅ |

### Risk

LitBridge's core is "literature matching + citation suggestion", which feels more like a productivity tool (Overwhelmed Student territory), but it doesn't perfectly match the deadline/task-management framing of Overwhelmed Student either.

Judges may push back: **"This helps people writing papers, not a student who is struggling to learn."**

---

## Possible adjustments

### Option A: tweak positioning to fit Struggling Learner

Reframe as a "reading-comprehension assistant":
- Upload a batch of paper PDFs (reading material)
- Student types "I don't understand the attention mechanism in Transformers"
- System finds relevant sections from the paper library, **summarises and explains**, and cites the source
- Becomes: **"help students find and understand relevant content within a large reading list"**

### Option B: pivot to The Overwhelmed Student

Reframe the pain point:
- "Grad students are drowning in 30 papers and don't know which ones are relevant to their research"
- LitBridge = literature filter + priority ranking
- More natural, but still not a perfect fit

### Option C (recommended): dual framing

Keep the LitBridge name and core unchanged, but pitch it as:

> "The Struggling Learner who is drowning in reading lists and doesn't know which papers actually matter for their assignment."

Reframe "find a citation" as "find the 3 papers you actually need to read out of 30", emphasising **"helping you read the right thing"** instead of "helping you cite". In the demo, show Topic → most relevant literature first (learning-oriented), then draft → citation suggestions (writing-oriented).

---

## Scoring summary

| Dimension | Score | Note |
|-----------|-------|------|
| Theme fit | ⚠️ 3/5 | Function leans productivity; needs re-framed narrative |
| Not a chatbot | ✅ 5/5 | Definitely not |
| Clear workflow | ✅ 5/5 | Input → process → output is crisp |
| Demoable in 90s | ✅ 4/5 | Need to prep mock data |
| Necessity of AI | ✅ 5/5 | Semantic matching and summarisation require AI |
| Feasible in 8h | ✅ 4/5 | RAG pipelines are mature, Streamlit gets UI fast |

### Key takeaway

Don't position LitBridge as a "citation manager". Position it as **"help students find the few papers that actually matter in a sea of literature"**. Judges are buying the story of "help a struggling student", not "save time for someone writing a paper".
