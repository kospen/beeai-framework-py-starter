# Guardrails v1 Spec

## Goal & Non-goals
Goal: Provide a post-answer validation layer that checks whether a final LLM answer is covered by retrieved context chunks ([C1]...[Cn]) and returns a deterministic PASS/WARN/REFUSE outcome.

Non-goals:
- No ingest changes.
- No Qdrant schema changes.
- No agents.
- No orchestration loop.

## Inputs / Outputs
Inputs and outputs reference the pseudo-types defined in `tmp_rag_guardrails.py`.

Input (GuardrailsInput):
- answer_text: str
- retrieved_chunks: list[RetrievedChunk]
- prompt_context_string: str
- citations: list[str]

Output (GuardrailsResult):
- status: "PASS" | "WARN" | "REFUSE"
- reasons: list[GuardrailsReason]
- uncovered_claims: list[str]
- citation_density: float
- supported_claims: int
- total_claims: int

## Metrics Definitions
- citation_density: citations_per_sentence = count(citations) / max(1, claim_count)
- claim_count heuristic: number of non-trivial claims derived from answer_text (see rules below)
- uncovered_claim: a non-trivial claim with no mapped evidence in cited chunks
- supported_claim: a non-trivial claim that maps to at least one cited chunk above similarity threshold

## Decision Rules (Deterministic)
Evaluation order:
1) If refuse_on_no_citations is true and citations is empty -> REFUSE.
2) If mapping fails (no viable claim-to-evidence alignment) -> REFUSE.
3) If uncovered_claims > max_uncovered_claims OR uncovered_claims / max(1, total_claims) > max_uncovered_ratio -> REFUSE.
4) If citation_density < min_citation_density -> WARN.
5) If uncovered_claims > 0 -> WARN.
6) Else -> PASS.

Threshold placeholders:
- min_citation_density = <TBD>
- max_uncovered_claims = <TBD>
- max_uncovered_ratio = <TBD>
- min_similarity_for_mapping = <TBD>

## Config Parameters (Placeholders)
- refuse_on_no_citations: <TBD>
- min_citation_density: <TBD>
- max_uncovered_claims: <TBD>
- max_uncovered_ratio: <TBD>
- min_similarity_for_mapping: <TBD>

## Edge Cases
- Boilerplate sentences: ignore for claim_count (e.g., "I cannot find that in the context.").
- Lists/bullets: each bullet is a separate claim unless clearly a fragment.
- Multi-citation claims: allow multiple [C#] tags; any valid mapping is sufficient.
- Short answers: if 1-2 sentences, claim_count is at least 1.
- Answers that only restate the question: treat as a claim and require citation coverage.

## Integration Contract (tmp_llm_answer_generator.py)
Upstream must pass: answer_text, retrieved_chunks, and prompt_context_string.
Downstream returns: GuardrailsResult with status, reasons, and coverage metrics.
