# LitBridge 📚🔗

> Your literature library × your paper — AI connects them.

LitBridge helps students **find the most relevant papers from their reading list** and understand which ones actually matter for their assignment or research topic. No more drowning in 30 PDFs.

Built for the **ANU AI Buildathon 2026**.

## Features

- **Smart Cite-Back**: Upload a draft paper → get AI-recommended citations from your library, matched paragraph by paragraph
- **Topic Search**: Enter a research question → get summaries of the most relevant papers, with source excerpts
- **RAG Pipeline**: Academic-grade retrieval with section-aware chunking and semantic matching

## Tech Stack

- **Frontend**: Streamlit
- **PDF Parsing**: PyMuPDF
- **Embeddings**: Anthropic Voyage (via API) / Sentence-Transformers (local)
- **Vector DB**: ChromaDB
- **LLM**: Claude 3.5 Sonnet (Anthropic)

## Getting Started

```bash
# Clone
git clone https://github.com/tianliang-tl/litbridge.git
cd litbridge

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

## Team

Built with ❤️ for ANU AIMSOC & ANUEC AI Buildathon.
