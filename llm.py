"""Claude wrapper: topic summary + cite-back JSON, with parsing fallbacks."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import anthropic

MODEL = "claude-haiku-4-5"
REQUEST_TIMEOUT_SECONDS = 30.0


@dataclass
class CiteBackVerdict:
    """One citation candidate after Claude's relevance judgement."""
    file: str
    page: int
    snippet: str
    relevance: float  # 0..1
    reason: str


def _client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)


def _extract_json(text: str) -> dict | list:
    """Extract first JSON object/array from possibly chatty model output."""
    text = text.strip()
    # Strip ```json ... ``` fences
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    # Greedy match
    match = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in: {text[:200]}")
    return json.loads(match.group(0))


def topic_summary(api_key: str, topic: str, hits: list[tuple]) -> str:
    """Feature B: synthesize a short literature summary from retrieved chunks.
    `hits` is list of (Chunk, score)."""
    client = _client(api_key)
    sources = "\n\n".join(
        f"[{i+1}] {c.file} (p.{c.page})\n{c.text}" for i, (c, _) in enumerate(hits)
    )
    prompt = f"""You are a research assistant. Given the topic and source excerpts below, write a concise (4-6 sentences) literature summary that ONLY uses information present in the sources. Cite sources inline like [1], [2]. Do not invent facts.

Topic: {topic}

Sources:
{sources}

Summary:"""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def cite_back(api_key: str, paragraph: str, hits: list[tuple]) -> list[CiteBackVerdict]:
    """Feature A: ask Claude to score each candidate's relevance to the paragraph.
    Returns list of verdicts sorted by relevance desc."""
    client = _client(api_key)
    candidates = "\n\n".join(
        f"[{i+1}] {c.file} (p.{c.page})\n{c.text[:600]}" for i, (c, _) in enumerate(hits)
    )
    prompt = f"""You are an academic citation assistant. The paragraph below is from a paper draft. For each candidate excerpt, judge how well it supports a citation in this paragraph.

Output a JSON array of objects with fields:
  - id (int, the [N] index)
  - relevance (float 0..1)
  - reason (one short sentence)

Output ONLY the JSON array, no commentary.

Paragraph:
{paragraph}

Candidates:
{candidates}"""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text
    try:
        scored = _extract_json(raw)
    except (ValueError, json.JSONDecodeError):
        # Fallback: use raw retrieval scores
        return [
            CiteBackVerdict(c.file, c.page, c.text[:300], score, "(retrieval score only)")
            for c, score in hits
        ]

    verdicts = []
    for s in scored:
        try:
            idx = int(s["id"]) - 1
            if 0 <= idx < len(hits):
                c, _ = hits[idx]
                verdicts.append(
                    CiteBackVerdict(
                        file=c.file,
                        page=c.page,
                        snippet=c.text[:300],
                        relevance=float(s.get("relevance", 0.0)),
                        reason=str(s.get("reason", "")),
                    )
                )
        except (KeyError, ValueError, TypeError):
            continue
    verdicts.sort(key=lambda v: -v.relevance)
    return verdicts
