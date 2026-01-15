import re
from typing import Any, Dict, List, Set

from .utils import _build_chunk_lookup, _extract_citations, _split_into_claims, _tokenize

# Guardrails v2 thresholds (Phase 2): used only when explicitly enabled.
V2_DEDUP_MAX_SINGLE_CHUNK_CITATION_SHARE = 0.80
V2_DEDUP_MIN_TOTAL_CITATIONS = 3

# Guardrails v2 flags (Phase 1): disabled by default; used only when explicitly enabled.
ENABLE_V2_SEMANTIC_SUPPORT_CHECK = False
ENABLE_V2_CITATION_DEDUP_PENALTY = False
ENABLE_V2_STRICT_CLAIM_EXTRACTION = False
ENABLE_V2_CLAIM_CITATION_ALIGNMENT = False


def _v2_apply_citation_dedup_penalty(metrics: Dict[str, Any], reasons: List[Dict[str, Any]]) -> None:
    if not ENABLE_V2_CITATION_DEDUP_PENALTY:
        return

    citations_by_chunk = metrics.get("citations_by_chunk")
    if not isinstance(citations_by_chunk, dict) or not citations_by_chunk:
        return

    citations_count = metrics.get("citations_count_total", metrics.get("citations_count", 0))
    if citations_count < V2_DEDUP_MIN_TOTAL_CITATIONS:
        return

    max_share = max(citations_by_chunk.values()) / max(1, citations_count)
    if max_share > V2_DEDUP_MAX_SINGLE_CHUNK_CITATION_SHARE:
        reasons.append(
            {
                "code": "CITATION_DEDUP_DOMINANCE",
                "message": "Citations are overly concentrated on a single chunk.",
                "details": {
                    "max_share": round(max_share, 2),
                    "threshold": V2_DEDUP_MAX_SINGLE_CHUNK_CITATION_SHARE,
                    "citations_count": citations_count,
                },
            }
        )


def _v2_semantic_support_check(
    answer_text: str, retrieved_chunks: List[Dict[str, Any]], metrics: Dict[str, Any], reasons: List[Dict[str, Any]]
) -> None:
    if not metrics.get("enable_v2_semantic_support_check", False):
        return

    percent_pattern = re.compile(r"\b\d+(?:\.\d+)?%\b")
    percents = percent_pattern.findall(answer_text)
    chunk_text = " ".join(str(chunk.get("text", "")) for chunk in retrieved_chunks)
    unsupported: List[str] = []
    if percents:
        for pct in percents:
            if pct not in chunk_text:
                unsupported.append(pct)
    else:
        chunk_tokens: Set[str] = set()
        for chunk in retrieved_chunks:
            chunk_tokens |= _tokenize(str(chunk.get("text", "")))
        answer_tokens = _tokenize(answer_text)
        stopwords = {
            "the",
            "and",
            "or",
            "is",
            "are",
            "was",
            "were",
            "a",
            "an",
            "to",
            "of",
            "in",
            "on",
            "for",
            "with",
            "as",
            "at",
            "by",
            "from",
            "that",
            "this",
            "it",
            "its",
            "be",
            "not",
            "only",
        }
        for token in answer_tokens:
            if token in stopwords:
                continue
            if token.startswith("c") and token[1:].isdigit():
                continue
            if token not in chunk_tokens:
                unsupported.append(token)
                break

    if unsupported:
        reasons.append(
            {
                "code": "SEMANTIC_SUPPORT_WEAK",
                "message": "Answer contains claims not supported by retrieved chunks.",
                "details": {"unsupported": unsupported},
            }
        )


def _v2_strict_claim_extraction_check(
    answer_text: str, retrieved_chunks: List[Dict[str, Any]], metrics: Dict[str, Any], reasons: List[Dict[str, Any]]
) -> None:
    if not metrics.get("enable_v2_strict_claim_extraction", False):
        return

    text_no_citations = re.sub(r"\[C\d+\]", "", answer_text)
    percent_pattern = re.compile(r"\b\d+(?:\.\d+)?%\b")
    years_pattern = re.compile(r"\b\d+\s+years?\b", re.IGNORECASE)
    explicit_claims: List[str] = []

    explicit_claims.extend(percent_pattern.findall(text_no_citations))
    explicit_claims.extend(years_pattern.findall(text_no_citations))

    absolutes = ["always", "guarantees", "guarantee", "all", "never"]
    for word in absolutes:
        if re.search(rf"\b{re.escape(word)}\b", text_no_citations, flags=re.IGNORECASE):
            explicit_claims.append(word)

    if not explicit_claims:
        return

    chunk_texts = [str(chunk.get("text", "")) for chunk in retrieved_chunks]
    unsupported: List[str] = []
    for claim in explicit_claims:
        supported = False
        pattern = re.compile(rf"\b{re.escape(claim)}\b", flags=re.IGNORECASE)
        for chunk_text in chunk_texts:
            if pattern.search(chunk_text):
                supported = True
                break
        if not supported:
            unsupported.append(claim)

    if unsupported:
        reasons.append(
            {
                "code": "UNSUPPORTED_EXPLICIT_CLAIM",
                "message": "Explicit claims are not supported by retrieved chunks.",
                "details": {"unsupported": unsupported},
            }
        )


def _v2_claim_citation_alignment_check(
    answer_text: str, retrieved_chunks: List[Dict[str, Any]], metrics: Dict[str, Any], reasons: List[Dict[str, Any]]
) -> None:
    if not metrics.get("enable_v2_claim_citation_alignment", False):
        return

    percent_pattern = re.compile(r"\b\d+(?:\.\d+)?%\b")
    years_pattern = re.compile(r"\b\d+\s+years?\b", re.IGNORECASE)
    chunk_lookup = _build_chunk_lookup(retrieved_chunks)
    unsupported: List[str] = []

    for claim in _split_into_claims(answer_text):
        claim_citations = _extract_citations(claim)
        if not claim_citations:
            continue
        claim_text = re.sub(r"\[C\d+\]", "", claim)
        numeric_tokens = percent_pattern.findall(claim_text)
        numeric_tokens.extend(years_pattern.findall(claim_text))
        if not numeric_tokens:
            continue

        supported = False
        for cite_id in claim_citations:
            chunk = chunk_lookup.get(cite_id)
            if not chunk:
                continue
            chunk_text = str(chunk.get("text", ""))
            for token in numeric_tokens:
                pattern = re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE)
                if pattern.search(chunk_text):
                    supported = True
                    break
            if supported:
                break

        if not supported:
            unsupported.extend(numeric_tokens)

    if unsupported:
        reasons.append(
            {
                "code": "CLAIM_CITATION_MISMATCH",
                "message": "Cited chunks do not support explicit numeric claims.",
                "details": {"unsupported": unsupported},
            }
        )
