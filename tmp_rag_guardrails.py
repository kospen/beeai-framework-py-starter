# Guardrails v1 (RAG v2) - Post-answer validation layer (skeleton only)
# Purpose: validate whether the final LLM answer is covered by retrieved context chunks [C1]...[Cn].
# SPEC SOURCE OF TRUTH: docs/guardrails_v1_spec.md (implementation MUST follow this spec 1:1)
#
# Architecture outline (planned):
# - Input: LLM final answer + prompt payload context/citations
# - Process: extract claims, map to cited chunks, assess coverage
# - Output: PASS / WARN / REFUSE with reasons and metadata
#
# CONTRACT (comments-only, pseudo-types)
# Canonical data shapes:
# - RetrievedChunk:
#   - id: str  # canonical chunk id like "C1"
#   - score: float
#   - source_file: str
#   - type: str
#   - topic: str
#   - chunk_index: int
#   - text: str
# - GuardrailsInput:
#   - answer_text: str
#   - retrieved_chunks: list[RetrievedChunk]
#   - prompt_context_string: str
#   - citations: list[str]  # extracted citation ids like ["C1", "C2"]
# - GuardrailsReason:
#   - code: str  # e.g., "NO_CITATIONS", "LOW_CITATION_DENSITY", "UNSUPPORTED_CLAIMS"
#   - message: str
#   - related_chunk_ids: list[str]
#   - details: dict  # optional extra metadata
# - GuardrailsResult:
#   - status: str  # allowed: "PASS" | "WARN" | "REFUSE"
#   - reasons: list[GuardrailsReason]
#   - uncovered_claims: list[str]
#   - citation_density: float
#   - supported_claims: int
#   - total_claims: int
#
# Allowed statuses: "PASS", "WARN", "REFUSE"
#
# Required fields:
# - RetrievedChunk: id, text, source_file, type, topic, chunk_index, score
# - GuardrailsInput: answer_text, retrieved_chunks, prompt_context_string, citations
# - GuardrailsReason: code, message, related_chunk_ids
# - GuardrailsResult: status, reasons, uncovered_claims, citation_density, supported_claims, total_claims
#
# Deterministic rules:
# - PASS: all non-trivial claims are supported by cited chunks.
# - WARN: minor uncovered claims or low citation density.
# - REFUSE: no citations OR too many uncovered claims OR failed mapping.
#
# Integration contract (single sentence):
# Upstream must pass answer_text, retrieved_chunks, and prompt_context_string; downstream returns a GuardrailsResult.
#
# TODO: Define inputs/outputs contract
#   - inputs: answer_text, retrieved_chunks (with ids), prompt_payload context
#   - outputs: status (PASS/WARN/REFUSE), reasons[], missing_citations[], confidence, debug metadata
#
# TODO: Coverage-check strategy options
#   - citation presence check: ensure each paragraph/claim has [C#] tags
#   - claim-to-evidence mapping: align statements to chunk text similarity/overlap
#   - whitelist/allowed hallucination categories (e.g., boilerplate disclaimers)
#   - handle multi-citation claims and partial coverage
#
# TODO: Thresholds/config placeholders
#   - min_citation_density (citations per N sentences)
#   - max_uncovered_claims
#   - similarity thresholds for claim-to-evidence matches
#   - refuse_on_no_citations (bool)
#
# TODO: Integration points with tmp_llm_answer_generator.py
#   - post-processing hook after model answer is generated
#   - pass prompt_payload + retrieved_chunks + answer_text into guardrails
#   - route WARN/REFUSE to caller with messaging/metadata
#
# TODO: Logging/telemetry notes
#   - log guardrail decision, missing citations, and evidence links
#   - include trace IDs for run correlation
#   - avoid logging raw sensitive content
#
# TODO: Minimal CLI hook placeholder
#   - e.g., python tmp_rag_guardrails.py --check "<answer>" --context "<context>"

# IMPLEMENTATION PLAN (comments-only)
# 1) Extract citations from answer_text ([C#] parsing).
# 2) Split answer_text into claims (heuristic rules).
# 3) Ignore boilerplate / non-claim sentences.
# 4) For each claim: map to cited chunks (similarity/overlap).
# 5) Compute metrics (citation_density, supported_claims, uncovered_claims).
# 6) Apply deterministic decision rules in exact order (REFUSE -> WARN -> PASS).
# 7) Build GuardrailsResult with reasons + metadata.
# 8) Return result to caller.
