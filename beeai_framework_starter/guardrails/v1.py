from typing import Any, Dict, List, Optional, Set, Tuple

from .utils import _build_chunk_lookup, _extract_citations, _overlap_ratio, _tokenize

REFUSE_ON_NO_CITATIONS = True
MIN_CITATION_DENSITY = 0.20
MAX_UNCOVERED_CLAIMS = 1
MAX_UNCOVERED_RATIO = 0.20
MIN_SIMILARITY_FOR_MAPPING = 0.20


def _map_claims_to_chunks(
    claims: List[str], retrieved_chunks: List[Dict[str, Any]], global_citations: List[str]
) -> List[Dict[str, Any]]:
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
    citations_count = metrics.get("citations_count", 0)
    citation_density = metrics.get("citation_density", 0.0)
    uncovered_claims_count = metrics.get("uncovered_claims_count", 0)
    uncovered_ratio = metrics.get("uncovered_ratio", 0.0)
    mapping_failed = bool(metrics.get("mapping_failed"))

    reasons: List[Dict[str, Any]] = []

    if REFUSE_ON_NO_CITATIONS and citations_count == 0:
        reasons.append(
            {
                "code": "NO_CITATIONS",
                "message": "No citations were found in the answer.",
                "related_chunk_ids": [],
            }
        )
        return "REFUSE", reasons

    if mapping_failed:
        reasons.append(
            {
                "code": "MAPPING_FAILED",
                "message": "Claim-to-evidence mapping failed.",
                "related_chunk_ids": [],
            }
        )
        return "REFUSE", reasons

    if uncovered_claims_count > MAX_UNCOVERED_CLAIMS or uncovered_ratio > MAX_UNCOVERED_RATIO:
        reasons.append(
            {
                "code": "UNSUPPORTED_CLAIMS",
                "message": "Too many claims are not supported by cited chunks.",
                "related_chunk_ids": [],
            }
        )
        return "REFUSE", reasons

    if citation_density < MIN_CITATION_DENSITY:
        reasons.append(
            {
                "code": "LOW_CITATION_DENSITY",
                "message": "Citation density is below the minimum threshold.",
                "related_chunk_ids": [],
            }
        )
        return "WARN", reasons

    if uncovered_claims_count > 0:
        reasons.append(
            {
                "code": "PARTIAL_COVERAGE",
                "message": "Some claims are not supported by cited chunks.",
                "related_chunk_ids": [],
            }
        )
        return "WARN", reasons

    return "PASS", reasons


def _build_result(status: str, reasons: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
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
