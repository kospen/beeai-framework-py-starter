# Guardrails v1 – Coverage Matrix

| Rule / Condition | Outcome | Covered by |
| --- | --- | --- |
| No citations | REFUSE | tmp_guardrails_smoketest.py, tmp_guardrails_cli_smoketest.py |
| Mapping failed | REFUSE | tmp_guardrails_smoketest.py |
| Too many unsupported claims | REFUSE | tmp_guardrails_smoketest.py |
| Low citation density | WARN | tmp_guardrails_smoketest.py |
| Partial coverage | WARN | tmp_guardrails_smoketest.py |
| Full coverage | PASS | tmp_guardrails_smoketest.py |

## Guardrails v2 — Citation Dedup Dominance (Phase 2)

When `ENABLE_V2_CITATION_DEDUP_PENALTY = True`, Guardrails evaluates
**citation concentration across retrieved chunks**.

### Behavior
- If citations are overly dominated by a single chunk:
  - Outcome is **downgraded from PASS → WARN**
  - Reason added: `CITATION_DEDUP_DOMINANCE`
- No REFUSE is triggered by this rule.
- When the flag is OFF, v1 behavior is unchanged.

### Rationale
This detects low-evidence diversity even when citations are formally present,
reducing false PASS cases caused by duplicated or clustered references.

### Status
- Deterministic
- Offline
- Covered by `tmp_guardrails_v2_flags_smoketest.py`
