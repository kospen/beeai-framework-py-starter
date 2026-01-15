"""
Guardrails v2 Phase 5 claim-citation alignment smoketest.
Expected: flag OFF -> PASS; flag ON -> WARN with CLAIM_CITATION_MISMATCH.
This test should fail until Phase 5 is implemented.
"""
import sys

from tmp_rag_guardrails_impl import run_guardrails


def _call_guardrails(answer_text, retrieved_chunks, prompt_context_string, flag):
    try:
        return run_guardrails(
            answer_text,
            retrieved_chunks,
            prompt_context_string,
            enable_v2_claim_citation_alignment=flag,
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


ANSWER = "Uptime is 99% [C1]. Warranty lasts 2 years [C2]."
CONTEXT = (
    "[C1]\ntext: Uptime is 99%.\n\n"
    "[C2]\ntext: Warranty details are not provided."
)
RETRIEVED_CHUNKS = [
    {"id": "C1", "text": "Uptime is 99%."},
    {"id": "C2", "text": "Warranty details are not provided."},
]


def main():
    outcome, reasons = run(False)
    print(f"[V2 OFF] outcome={outcome} reasons={reasons}")
    assert outcome == "PASS"
    assert outcome != "REFUSE"

    outcome, reasons = run(True)
    print(f"[V2 ON ] outcome={outcome} reasons={reasons}")
    assert outcome == "WARN"
    assert "CLAIM_CITATION_MISMATCH" in reasons
    assert outcome != "REFUSE"

    sys.exit(0)


if __name__ == "__main__":
    main()
