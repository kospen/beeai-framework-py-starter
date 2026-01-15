"""
Guardrails v2 Phase 4 strict claim extraction smoketest.
Phase 4 is intended to catch explicit claims that are not fully supported by context.
This test should fail until Phase 4 is implemented and the flag is honored.
"""
import sys

from tmp_rag_guardrails_impl import run_guardrails


def _call_guardrails(answer_text, retrieved_chunks, prompt_context_string, flag):
    try:
        return run_guardrails(
            answer_text,
            retrieved_chunks,
            prompt_context_string,
            enable_v2_strict_claim_extraction=flag,
        )
    except TypeError:
        return run_guardrails(answer_text, retrieved_chunks, prompt_context_string)


def _normalize_reasons(result):
    reasons_raw = (result or {}).get("reasons", []) or []
    reasons = []
    for item in reasons_raw:
        if isinstance(item, dict):
            reasons.append(item.get("code") or item.get("message") or str(item))
        else:
            reasons.append(str(item))
    return reasons


def run(flag):
    result = _call_guardrails(ANSWER, RETRIEVED_CHUNKS, CONTEXT, flag)
    outcome = (result or {}).get("status", "")
    reasons = _normalize_reasons(result)
    return outcome, reasons


ANSWER = "The device supports 99% uptime [C1]. The warranty lasts 2 years [C1]."
CONTEXT = (
    "[C1]\ntext: The device supports 95% uptime. Warranty information is not provided."
)
RETRIEVED_CHUNKS = [
    {"id": "C1", "text": "The device supports 95% uptime. Warranty information is not provided."}
]


def main():
    outcome, reasons = run(False)
    print(f"[V2 OFF] outcome={outcome} reasons={reasons}")
    assert outcome == "PASS"
    assert outcome != "REFUSE"

    outcome, reasons = run(True)
    print(f"[V2 ON ] outcome={outcome} reasons={reasons}")
    assert outcome == "WARN"
    assert "UNSUPPORTED_EXPLICIT_CLAIM" in reasons
    assert outcome != "REFUSE"

    sys.exit(0)


if __name__ == "__main__":
    main()
