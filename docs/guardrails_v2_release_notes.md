# Guardrails v2.0 Release Notes

## What shipped in v2.0 (Phase 2–6)
- Phase 2: citation dedup penalty behind flag (PASS → WARN when citations over-concentrate on one chunk)
- Phase 3: semantic support check behind flag (PASS → WARN on weak support)
- Phase 4: strict claim extraction behind flag (PASS → WARN on unsupported explicit claims)
- Phase 5: claim–citation alignment behind flag (PASS → WARN when cited chunks do not support numeric claims)
- Phase 6: mixed-claims handling (supported + unsupported explicit claims still WARN)

## Flags (default OFF)
- ENABLE_V2_CITATION_DEDUP_PENALTY
- ENABLE_V2_SEMANTIC_SUPPORT_CHECK
- ENABLE_V2_STRICT_CLAIM_EXTRACTION
- ENABLE_V2_CLAIM_CITATION_ALIGNMENT

## Outcomes
- PASS/WARN/REFUSE remain unchanged for v1 when flags are OFF
- v2 introduces WARN-only penalties; no new REFUSE paths are added
- PASS can be downgraded to WARN when a v2 rule triggers

## Tests
- v1: tmp_guardrails_smoketest.py, tmp_guardrails_edge_smoketest.py, tmp_guardrails_cli_smoketest.py
- v2: tmp_guardrails_v2_flags_smoketest.py, tmp_guardrails_v2_semantic_smoketest.py,
  tmp_guardrails_v2_strict_claims_smoketest.py, tmp_guardrails_v2_claim_citation_alignment_smoketest.py,
  tmp_guardrails_v2_mixed_claims_smoketest.py

## Known limitations
- Duplicated citations may PASS even with weak semantic support when v2 flags are OFF
