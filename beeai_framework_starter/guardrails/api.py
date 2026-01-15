from typing import Any, Dict, List, Optional

from . import v1, v2
from .utils import _build_chunk_lookup, _extract_citations, _filter_non_claims, _split_into_claims


def run_guardrails(
    answer_text: str,
    retrieved_chunks: List[Dict[str, Any]],
    prompt_context_string: str,
    enable_v2_semantic_support_check: Optional[bool] = None,
    enable_v2_strict_claim_extraction: Optional[bool] = None,
    enable_v2_claim_citation_alignment: Optional[bool] = None,
) -> Dict[str, Any]:
    citations = _extract_citations(answer_text)
    claims = _split_into_claims(answer_text)
    claims = _filter_non_claims(claims)
    mapped = v1._map_claims_to_chunks(claims, retrieved_chunks, citations)
    metrics = v1._compute_metrics(mapped, citations)
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

    if enable_v2_semantic_support_check is None:
        metrics["enable_v2_semantic_support_check"] = v2.ENABLE_V2_SEMANTIC_SUPPORT_CHECK
    else:
        metrics["enable_v2_semantic_support_check"] = enable_v2_semantic_support_check
    if enable_v2_strict_claim_extraction is None:
        metrics["enable_v2_strict_claim_extraction"] = v2.ENABLE_V2_STRICT_CLAIM_EXTRACTION
    else:
        metrics["enable_v2_strict_claim_extraction"] = enable_v2_strict_claim_extraction
    if enable_v2_claim_citation_alignment is None:
        metrics["enable_v2_claim_citation_alignment"] = v2.ENABLE_V2_CLAIM_CITATION_ALIGNMENT
    else:
        metrics["enable_v2_claim_citation_alignment"] = enable_v2_claim_citation_alignment

    metrics["mapping_failed"] = mapping_failed
    status, reasons = v1._apply_decision_rules(metrics)
    v2._v2_semantic_support_check(answer_text, retrieved_chunks, metrics, reasons)
    v2._v2_strict_claim_extraction_check(answer_text, retrieved_chunks, metrics, reasons)
    v2._v2_claim_citation_alignment_check(answer_text, retrieved_chunks, metrics, reasons)
    v2._v2_apply_citation_dedup_penalty(metrics, reasons)
    if status == "PASS" and any(
        r.get("code")
        in (
            "CITATION_DEDUP_DOMINANCE",
            "SEMANTIC_SUPPORT_WEAK",
            "UNSUPPORTED_EXPLICIT_CLAIM",
            "CLAIM_CITATION_MISMATCH",
        )
        for r in reasons
    ):
        status = "WARN"
    return v1._build_result(status, reasons, metrics)
