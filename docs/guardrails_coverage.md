# Guardrails v1 – Coverage Matrix

| Rule / Condition | Outcome | Covered by |
| --- | --- | --- |
| No citations | REFUSE | tmp_guardrails_smoketest.py, tmp_guardrails_cli_smoketest.py |
| Mapping failed | REFUSE | tmp_guardrails_smoketest.py |
| Too many unsupported claims | REFUSE | tmp_guardrails_smoketest.py |
| Low citation density | WARN | tmp_guardrails_smoketest.py |
| Partial coverage | WARN | tmp_guardrails_smoketest.py |
| Full coverage | PASS | tmp_guardrails_smoketest.py |
