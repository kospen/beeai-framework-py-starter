# SPEC SOURCE OF TRUTH: docs/guardrails_v1_spec.md (implementation MUST follow this spec 1:1)

import re
from typing import Any, Dict, List, Optional, Set, Tuple


def run_guardrails(
    answer_text: str,
    retrieved_chunks: List[Dict[str, Any]],
    prompt_context_string: str,
    enable_v2_semantic_support_check: Optional[bool] = None,
) -> Dict[str, Any]:
    """Run Guardrails v1 validation and return a GuardrailsResult-shaped dict."""
    # TODO: Orchestrate guardrails steps per the spec and return result.
    citations = _extract_citations(answer_text)
    claims = _split_into_claims(answer_text)
    claims = _filter_non_claims(claims)
    mapped = _map_claims_to_chunks(claims, retrieved_chunks, citations)
    metrics = _compute_metrics(mapped, citations)
    if enable_v2_semantic_support_check is None:
        metrics["enable_v2_semantic_support_check"] = ENABLE_V2_SEMANTIC_SUPPORT_CHECK
    else:
        metrics["enable_v2_semantic_support_check"] = enable_v2_semantic_support_check
    citations_by_chunk: Dict[str, int] = {}
    total_citations = 0
    for cite_id in citations:
        count = answer_text.count(f"[{cite_id}]")
        if count:
            citations_by_chunk[cite_id] = count
            total_citations += count
    metrics["citations_by_chunk"] = citations_by_chunk
    metrics["citations_count_total"] = total_citations

    mapping_failed = False
    if claims:
        if not retrieved_chunks:
            mapping_failed = True
        else:
            cited_ids = set(citations)
            available_ids = _build_chunk_lookup(retrieved_chunks).keys()
            if cited_ids and not (cited_ids & set(available_ids)):
                mapping_failed = True

    metrics["mapping_failed"] = mapping_failed
    status, reasons = _apply_decision_rules(metrics)
    _v2_semantic_support_check(answer_text, retrieved_chunks, metrics, reasons)
    _v2_apply_citation_dedup_penalty(metrics, reasons)
    if status == "PASS" and any(
        r.get("code") in ("CITATION_DEDUP_DOMINANCE", "SEMANTIC_SUPPORT_WEAK") for r in reasons
    ):
        status = "WARN"
    return _build_result(status, reasons, metrics)


def _extract_citations(answer_text: str) -> List[str]:
    citations: List[str] = []
    seen: set[str] = set()
    i = 0
    text_len = len(answer_text)

    while i < text_len:
        if answer_text[i] == "[" and i + 2 < text_len and answer_text[i + 1] == "C":
            j = i + 2
            while j < text_len and answer_text[j].isdigit():
                j += 1
            if j > i + 2 and j < text_len and answer_text[j] == "]":
                cite_id = answer_text[i + 1 : j]
                if cite_id not in seen:
                    citations.append(cite_id)
                    seen.add(cite_id)
                i = j + 1
                continue
        i += 1

    return citations


def _split_into_claims(answer_text: str) -> List[str]:
    claims: List[str] = []
    buf: list[str] = []

    for ch in answer_text:
        if ch == "\n" or ch in ".?!":
            segment = "".join(buf).strip()
            if segment:
                claims.append(segment)
            buf = []
        else:
            buf.append(ch)

    tail = "".join(buf).strip()
    if tail:
        claims.append(tail)

    return claims


def _filter_non_claims(claims: List[str]) -> List[str]:
    filtered: List[str] = []
    prefixes = [
        "i cannot",
        "i can't",
        "cannot find",
        "not found in the context",
        "insufficient context",
        "i don't have",
        "i do not have",
        "as an ai",
        "i am an ai",
        "i can’t",
    ]

    for claim in claims:
        stripped = claim.strip()
        if len(stripped) < 8:
            continue
        if not any(ch.isalnum() for ch in stripped):
            continue

        lowered = stripped.lower()
        if any(lowered.startswith(prefix) for prefix in prefixes):
            continue

        filtered.append(stripped)

    return filtered


def _map_claims_to_chunks(
    claims: List[str], retrieved_chunks: List[Dict[str, Any]], global_citations: List[str]
) -> List[Dict[str, Any]]:
    # TODO: Map each claim to cited chunk(s) using similarity/overlap.
    chunk_lookup = _build_chunk_lookup(retrieved_chunks)
    mapped: List[Dict[str, Any]] = []

    for claim in claims:
        local_citations = _extract_citations(claim)
        cited_chunk_ids = local_citations if local_citations else list(global_citations)
        claim_tokens = _tokenize(claim)
        best_chunk_id: Optional[str] = None
        best_score = 0.0

        for chunk_id in cited_chunk_ids:
            chunk = chunk_lookup.get(chunk_id)
            if not chunk:
                continue
            chunk_text = str(chunk.get("text", ""))
            chunk_tokens = _tokenize(chunk_text)
            score = _overlap_ratio(claim_tokens, chunk_tokens)
            if score > best_score:
                best_score = score
                best_chunk_id = chunk_id

        is_supported = bool(cited_chunk_ids) and best_score >= MIN_SIMILARITY_FOR_MAPPING
        mapped.append(
            {
                "claim": claim,
                "cited_chunk_ids": cited_chunk_ids,
                "best_chunk_id": best_chunk_id,
                "best_score": best_score,
                "is_supported": is_supported,
            }
        )

    return mapped


def _compute_metrics(mapped_claims: List[Dict[str, Any]], citations: List[str]) -> Dict[str, Any]:
    # TODO: Compute citation_density, supported_claims, uncovered_claims, total_claims.
    total_claims = len(mapped_claims)
    supported_claims = sum(1 for item in mapped_claims if item.get("is_supported"))
    uncovered_claims = [item.get("claim", "") for item in mapped_claims if not item.get("is_supported")]
    citation_density = len(citations) / max(1, total_claims)

    return {
        "citations": citations,
        "citations_count": len(citations),
        "total_claims": total_claims,
        "supported_claims": supported_claims,
        "uncovered_claims": uncovered_claims,
        "uncovered_claims_count": len(uncovered_claims),
        "uncovered_ratio": (len(uncovered_claims) / max(1, total_claims)),
        "citation_density": citation_density,
    }


def _apply_decision_rules(metrics: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    # TODO: Apply deterministic PASS/WARN/REFUSE rules in spec order.
    citations_count = metrics.get("citations_count", 0)
    citation_density = metrics.get("citation_density", 0.0)
    uncovered_claims_count = metrics.get("uncovered_claims_count", 0)
    uncovered_ratio = metrics.get("uncovered_ratio", 0.0)
    mapping_failed = bool(metrics.get("mapping_failed"))

    reasons: List[Dict[str, Any]] = []

    if REFUSE_ON_NO_CITATIONS and citations_count == 0:
        # REFUSE when no citations are found; covered by tmp_guardrails_smoketest.py.
        reasons.append(
            {
                "code": "NO_CITATIONS",
                "message": "No citations were found in the answer.",
                "related_chunk_ids": [],
            }
        )
        return "REFUSE", reasons

    if mapping_failed:
        # REFUSE when claim-to-evidence mapping fails; covered by tmp_guardrails_smoketest.py.
        reasons.append(
            {
                "code": "MAPPING_FAILED",
                "message": "Claim-to-evidence mapping failed.",
                "related_chunk_ids": [],
            }
        )
        return "REFUSE", reasons

    if uncovered_claims_count > MAX_UNCOVERED_CLAIMS or uncovered_ratio > MAX_UNCOVERED_RATIO:
        # REFUSE when too many claims are unsupported; covered by tmp_guardrails_smoketest.py.
        reasons.append(
            {
                "code": "UNSUPPORTED_CLAIMS",
                "message": "Too many claims are not supported by cited chunks.",
                "related_chunk_ids": [],
            }
        )
        return "REFUSE", reasons

    if citation_density < MIN_CITATION_DENSITY:
        # WARN when citation density is below threshold; covered by tmp_guardrails_smoketest.py.
        reasons.append(
            {
                "code": "LOW_CITATION_DENSITY",
                "message": "Citation density is below the minimum threshold.",
                "related_chunk_ids": [],
            }
        )
        return "WARN", reasons

    if uncovered_claims_count > 0:
        # WARN when some claims lack support; covered by tmp_guardrails_smoketest.py.
        reasons.append(
            {
                "code": "PARTIAL_COVERAGE",
                "message": "Some claims are not supported by cited chunks.",
                "related_chunk_ids": [],
            }
        )
        return "WARN", reasons

    # PASS when no refusal or warning conditions apply; covered by tmp_guardrails_smoketest.py.
    return "PASS", reasons


def _v2_apply_citation_dedup_penalty(metrics: Dict[str, Any], reasons: List[Dict[str, Any]]) -> None:
    """
    Phase 1: placeholder. If ENABLE_V2_CITATION_DEDUP_PENALTY is False -> return.
    If True -> currently do nothing (TODO in Phase 2).
    """
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
    """
    Phase 1: placeholder. If ENABLE_V2_SEMANTIC_SUPPORT_CHECK is False -> return.
    If True -> currently do nothing (TODO in Phase 2).
    """
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


def _build_result(status: str, reasons: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
    # TODO: Build GuardrailsResult with reasons and metadata.
    return {
        "status": status,
        "reasons": reasons,
        "uncovered_claims": metrics.get("uncovered_claims", []),
        "citation_density": metrics.get("citation_density", 0.0),
        "supported_claims": metrics.get("supported_claims", 0),
        "total_claims": metrics.get("total_claims", 0),
        "debug": {
            "citations": metrics.get("citations", []),
            "uncovered_ratio": metrics.get("uncovered_ratio", 0.0),
            "mapping_failed": metrics.get("mapping_failed", False),
        },
    }


REFUSE_ON_NO_CITATIONS = True
MIN_CITATION_DENSITY = 0.20
MAX_UNCOVERED_CLAIMS = 1
MAX_UNCOVERED_RATIO = 0.20
MIN_SIMILARITY_FOR_MAPPING = 0.20

# Guardrails v2 thresholds (Phase 2): used only when explicitly enabled.
V2_DEDUP_MAX_SINGLE_CHUNK_CITATION_SHARE = 0.80
V2_DEDUP_MIN_TOTAL_CITATIONS = 3

# Guardrails v2 flags (Phase 1): disabled by default; used only when explicitly enabled.
ENABLE_V2_SEMANTIC_SUPPORT_CHECK = False
ENABLE_V2_CITATION_DEDUP_PENALTY = False
ENABLE_V2_STRICT_CLAIM_EXTRACTION = False


def _build_chunk_lookup(retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for chunk in retrieved_chunks:
        chunk_id = chunk.get("id")
        if not chunk_id:
            chunk_index = chunk.get("chunk_index")
            if isinstance(chunk_index, int):
                chunk_id = f"C{chunk_index}"
        if isinstance(chunk_id, str) and chunk_id:
            lookup[chunk_id] = chunk
    return lookup


def _tokenize(text: str) -> Set[str]:
    tokens: List[str] = []
    buf: List[str] = []
    for ch in text.lower():
        if ch.isalnum():
            buf.append(ch)
        else:
            if buf:
                tokens.append("".join(buf))
                buf = []
    if buf:
        tokens.append("".join(buf))
    return set(tokens)


def _overlap_ratio(claim_tokens: Set[str], chunk_tokens: Set[str]) -> float:
    if not claim_tokens:
        return 0.0
    overlap = claim_tokens & chunk_tokens
    return len(overlap) / max(1, len(claim_tokens))
