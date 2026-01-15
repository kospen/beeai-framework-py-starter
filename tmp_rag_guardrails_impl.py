# SPEC SOURCE OF TRUTH: docs/guardrails_v1_spec.md (implementation MUST follow this spec 1:1)

from typing import Any, Dict, List, Optional, Set, Tuple

from beeai_framework_starter.guardrails import api as _api
from beeai_framework_starter.guardrails import utils as _utils
from beeai_framework_starter.guardrails import v1 as _v1
from beeai_framework_starter.guardrails import v2 as _v2


def run_guardrails(
    answer_text: str,
    retrieved_chunks: List[Dict[str, Any]],
    prompt_context_string: str,
    enable_v2_semantic_support_check: Optional[bool] = None,
    enable_v2_strict_claim_extraction: Optional[bool] = None,
    enable_v2_claim_citation_alignment: Optional[bool] = None,
) -> Dict[str, Any]:
    _sync_constants()
    return _api.run_guardrails(
        answer_text=answer_text,
        retrieved_chunks=retrieved_chunks,
        prompt_context_string=prompt_context_string,
        enable_v2_semantic_support_check=enable_v2_semantic_support_check,
        enable_v2_strict_claim_extraction=enable_v2_strict_claim_extraction,
        enable_v2_claim_citation_alignment=enable_v2_claim_citation_alignment,
    )


def _sync_constants() -> None:
    _v1.REFUSE_ON_NO_CITATIONS = REFUSE_ON_NO_CITATIONS
    _v1.MIN_CITATION_DENSITY = MIN_CITATION_DENSITY
    _v1.MAX_UNCOVERED_CLAIMS = MAX_UNCOVERED_CLAIMS
    _v1.MAX_UNCOVERED_RATIO = MAX_UNCOVERED_RATIO
    _v1.MIN_SIMILARITY_FOR_MAPPING = MIN_SIMILARITY_FOR_MAPPING

    _v2.V2_DEDUP_MAX_SINGLE_CHUNK_CITATION_SHARE = V2_DEDUP_MAX_SINGLE_CHUNK_CITATION_SHARE
    _v2.V2_DEDUP_MIN_TOTAL_CITATIONS = V2_DEDUP_MIN_TOTAL_CITATIONS
    _v2.ENABLE_V2_SEMANTIC_SUPPORT_CHECK = ENABLE_V2_SEMANTIC_SUPPORT_CHECK
    _v2.ENABLE_V2_CITATION_DEDUP_PENALTY = ENABLE_V2_CITATION_DEDUP_PENALTY
    _v2.ENABLE_V2_STRICT_CLAIM_EXTRACTION = ENABLE_V2_STRICT_CLAIM_EXTRACTION
    _v2.ENABLE_V2_CLAIM_CITATION_ALIGNMENT = ENABLE_V2_CLAIM_CITATION_ALIGNMENT


REFUSE_ON_NO_CITATIONS = True
MIN_CITATION_DENSITY = 0.20
MAX_UNCOVERED_CLAIMS = 1
MAX_UNCOVERED_RATIO = 0.20
MIN_SIMILARITY_FOR_MAPPING = 0.20

V2_DEDUP_MAX_SINGLE_CHUNK_CITATION_SHARE = 0.80
V2_DEDUP_MIN_TOTAL_CITATIONS = 3

ENABLE_V2_SEMANTIC_SUPPORT_CHECK = False
ENABLE_V2_CITATION_DEDUP_PENALTY = False
ENABLE_V2_STRICT_CLAIM_EXTRACTION = False
ENABLE_V2_CLAIM_CITATION_ALIGNMENT = False


def _extract_citations(answer_text: str) -> List[str]:
    return _utils._extract_citations(answer_text)


def _split_into_claims(answer_text: str) -> List[str]:
    return _utils._split_into_claims(answer_text)


def _filter_non_claims(claims: List[str]) -> List[str]:
    return _utils._filter_non_claims(claims)


def _map_claims_to_chunks(
    claims: List[str], retrieved_chunks: List[Dict[str, Any]], global_citations: List[str]
) -> List[Dict[str, Any]]:
    _sync_constants()
    return _v1._map_claims_to_chunks(claims, retrieved_chunks, global_citations)


def _compute_metrics(mapped_claims: List[Dict[str, Any]], citations: List[str]) -> Dict[str, Any]:
    _sync_constants()
    return _v1._compute_metrics(mapped_claims, citations)


def _apply_decision_rules(metrics: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    _sync_constants()
    return _v1._apply_decision_rules(metrics)


def _build_result(status: str, reasons: List[Dict[str, Any]], metrics: Dict[str, Any]) -> Dict[str, Any]:
    return _v1._build_result(status, reasons, metrics)


def _build_chunk_lookup(retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return _utils._build_chunk_lookup(retrieved_chunks)


def _tokenize(text: str) -> Set[str]:
    return _utils._tokenize(text)


def _overlap_ratio(claim_tokens: Set[str], chunk_tokens: Set[str]) -> float:
    return _utils._overlap_ratio(claim_tokens, chunk_tokens)


def _v2_apply_citation_dedup_penalty(metrics: Dict[str, Any], reasons: List[Dict[str, Any]]) -> None:
    _sync_constants()
    _v2._v2_apply_citation_dedup_penalty(metrics, reasons)


def _v2_semantic_support_check(
    answer_text: str, retrieved_chunks: List[Dict[str, Any]], metrics: Dict[str, Any], reasons: List[Dict[str, Any]]
) -> None:
    _sync_constants()
    _v2._v2_semantic_support_check(answer_text, retrieved_chunks, metrics, reasons)


def _v2_strict_claim_extraction_check(
    answer_text: str, retrieved_chunks: List[Dict[str, Any]], metrics: Dict[str, Any], reasons: List[Dict[str, Any]]
) -> None:
    _sync_constants()
    _v2._v2_strict_claim_extraction_check(answer_text, retrieved_chunks, metrics, reasons)


def _v2_claim_citation_alignment_check(
    answer_text: str, retrieved_chunks: List[Dict[str, Any]], metrics: Dict[str, Any], reasons: List[Dict[str, Any]]
) -> None:
    _sync_constants()
    _v2._v2_claim_citation_alignment_check(answer_text, retrieved_chunks, metrics, reasons)
