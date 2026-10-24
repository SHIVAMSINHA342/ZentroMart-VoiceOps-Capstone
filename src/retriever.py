"""Policy-aware retrieval for the ZentroMart knowledge base."""

import re
from datetime import date
from .kb_parser import parse_knowledge_sections

REFERENCE_DATE = date(2026, 10, 20)
ELECTRONICS_POLICY_CHANGE = date(2026, 8, 1)


def _terms(text):
    return set(re.findall(r"[a-z0-9]+", str(text).lower()))


def _historical_electronics_query(question):
    q = str(question).lower()

    historical_cues = (
        "before august 1", "before 1 august", "before aug 1",
        "before 2026-08-01", "before 01-08-2026",
        "delivered before", "delivery before", "delivered prior to",
        "before august", "prior to august 1", "prior to 1 august",
        "old policy", "previous policy", "historical policy",
        "10-day", "10 day", "ten-day", "ten day", "retv3-2"
    )
    return (
        any(cue in q for cue in historical_cues)
        and any(word in q for word in ("electronic", "accessor", "retv3-2"))
    )


def _score(question, section):
    query_terms = _terms(question)
    heading_terms = _terms(section.get("heading", ""))
    body_terms = _terms(section.get("text", ""))

    # Common words are deliberately given less influence.
    stop_words = {
        "the", "a", "an", "is", "are", "do", "does", "i", "my",
        "me", "for", "to", "of", "and", "in", "on", "what", "how",
        "can", "it", "be", "days", "day"
    }
    query_terms -= stop_words

    return (
        3 * len(query_terms & heading_terms)
        + len(query_terms & body_terms)
    )


def retrieve_sections(question, top_k=5):
    sections = parse_knowledge_sections()
    historical_case = _historical_electronics_query(question)
    results = []

    for section in sections:
        status = str(section.get("status", "unknown")).lower()
        section_id = str(section.get("section_id", ""))

        # Exclude superseded material by default.
        if status == "superseded":
            if not (historical_case and section_id == "RETv3-2"):
                continue

        score = _score(question, section)

        # Explicit historical electronics questions should retain the
        # current change notice and the old rule together.
        if historical_case and section_id == "RET-3":
            score += 20
        if historical_case and section_id == "RETv3-2":
            score += 20
        if score <= 0:
            continue

        results.append((score, section))

    results.sort(
        key=lambda item: (
            -item[0],
            item[1].get("status") != "current",
            item[1].get("section_id", "")
        )
    )

    return [
        {
            **section,
            "retrieval_score": score
        }
        for score, section in results[:max(1, int(top_k))]
    ]


def retrieve_policy_evidence(question, top_k=5):
    """Return retrieved sections with source IDs and policy status."""
    return [
        {
            "source_id": section["section_id"],
            "filename": section["filename"],
            "status": section["status"],
            "effective_from": section.get("effective_from"),
            "text": section["text"],
            "score": section["retrieval_score"]
        }
        for section in retrieve_sections(question, top_k=top_k)
    ]
