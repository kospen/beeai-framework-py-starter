"""
Guardrails v2 Phase 6 mixed-claims smoketest.
Intent: supported and unsupported explicit claims together should still WARN when v2 flags are on.
"""
import sys

from tmp_rag_guardrails_impl import run_guardrails


def _call_guardrails(answer_text, retrieved_chunks, prompt_context_string, enable_flags):
    if not enable_flags:
        try:
            return run_guardrails(answer_text, retrieved_chunks)
        except TypeError:
            return run_guardrails(answer_text, retrieved_chunks, prompt_context_string)
    try:
        return run_guardrails(
            answer_text,
            retrieved_chunks,
            prompt_context_string,
            enable_v2_strict_claim_extraction=True,
            enable_v2_claim_citation_alignment=True,
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


def run(enable_flags):
    result = _call_guardrails(ANSWER, RETRIEVED_CHUNKS, CONTEXT, enable_flags)
    outcome = (result or {}).get("status", "")
    reasons = _normalize_reasons(result)
    return outcome, reasons


ANSWER = "Uptime is 95% [C1]. Warranty lasts 2 years [C2]."
CONTEXT = (
    "[C1]\ntext: Uptime is 95%.\n\n"
    "[C2]\ntext: Warranty lasts years for coverage."
)
RETRIEVED_CHUNKS = [
    {"id": "C1", "text": "Uptime is 95%."},
    {"id": "C2", "text": "Warranty lasts years for coverage."},
]


def main():
    outcome, reasons = run(False)
    print(f"[V2 OFF] outcome={outcome} reasons={reasons}")
    assert outcome == "PASS"
    assert outcome != "REFUSE"

    outcome, reasons = run(True)
    print(f"[V2 ON ] outcome={outcome} reasons={reasons}")
    assert outcome == "WARN"
    assert any(
        code in reasons
        for code in ("UNSUPPORTED_EXPLICIT_CLAIM", "CLAIM_CITATION_MISMATCH", "SEMANTIC_SUPPORT_WEAK")
    )
    assert outcome != "REFUSE"

    sys.exit(0)


if __name__ == "__main__":
    main()
