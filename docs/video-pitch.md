# LitBridge - AI-Powered Literature Management for Students

## The Problem

Students are overwhelmed. They collect dozens of research papers for assignments but struggle with two critical tasks:

1. **Matching papers to their writing** — "I have 20 papers and a half-written essay. Which papers go where?"
2. **Building arguments from sources** — "I have a research question and a pile of PDFs. Which papers support my argument?"

Generic chatbots can summarize a single paper. But they can't connect YOUR library to YOUR writing. That's the gap LitBridge fills.

## The Solution: LitBridge

LitBridge is an AI-powered academic tool that connects your personal literature library with your research writing. It provides two core features designed specifically for the overwhelmed student.

### Feature 1: Smart Cite-Back (Draft → Library)

You're writing a literature review. You've uploaded your draft and your paper library. Click any paragraph in your draft — LitBridge's AI instantly finds the best-matching paper from your library, highlights the exact relevant passage, and lets you insert a citation with one click.

**How it works:**
- Three-pane workspace: your draft, the matched reference, and your paper library
- AI analyzes each paragraph and ranks every paper in your library by relevance
- Shows the specific source chunk with page numbers
- One-click citation insertion

### Feature 2: Topic Search (Question → Library)

You have a research question. LitBridge searches your entire library, reads the relevant sections, and writes a synthesized answer with inline citations [1][2] pointing to specific papers.

**How it works:**
- Ask any question about your research topic
- AI retrieves and reads relevant sections from your papers
- Returns a structured summary with clickable citations

## Technical Innovation

- **Section-aware chunking**: Automatically strips references and bibliography sections, keeping only substantive content
- **Local embeddings**: Runs sentence-transformers locally for privacy — no student data sent to third-party embedding services
- **Hybrid retrieval**: Combines semantic search with keyword fallback for robust matching
- **AI scoring with reasoning**: Claude doesn't just match — it explains WHY each match is relevant

## Built for the ANU AI Buildathon

**Category**: The Overwhelmed Student

**What LitBridge delivers:**
- **Clear workflow**: Upload papers → provide draft or topic → get organized results
- **Practical output**: Actionable citation suggestions and synthesized evidence summaries
- **Student-specific logic**: Not a generic RAG tool — purpose-built for academic writing workflows
- **Honest limitations**: Works best with English academic papers, limited to uploaded library content

## Live Demo

Try it at https://litbridge.streamlit.app/

Comes pre-loaded with a 13-paper sample library on LLM agents and a sample literature review draft for instant demonstration.
