# Guardrails v2 – Roadmap

## Goals
- Reduce false PASS when citations are duplicated but semantic support is weak
- Improve claim-to-evidence mapping robustness
- Keep v1 behavior backwards-compatible unless explicitly toggled

## Non-breaking upgrades (default off via flags)
- Semantic support check: require chunk text similarity / keyword overlap per claim
- Citation dedup penalty: if >X% citations point to same chunk, downgrade PASS->WARN
- Stricter uncovered-claim accounting: sentence-level claim extraction improvements

## Breaking changes (explicitly out of scope for v2)
- Replacing the entire mapping algorithm
- Adding external dependencies or online services

## Test plan
- Extend tmp_guardrails_edge_smoketest.py with a v2-flagged case that must WARN/REFUSE for duplicated citations
- Add one new deterministic smoketest file for v2 flags only

## Rollout
- Implement behind flags in tmp_rag_guardrails_impl.py
- Default flags disabled; enable in generator/CLI only when we decide
