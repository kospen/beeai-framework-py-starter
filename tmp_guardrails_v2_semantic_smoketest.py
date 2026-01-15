"""
Guardrails v2 Phase 3 semantic support smoketest.
Expected: flag OFF -> PASS; flag ON -> WARN with SEMANTIC_SUPPORT_WEAK reason.
"""
import sys

import tmp_rag_guardrails_impl as gri


def _call_guardrails(answer_text, retrieved_chunks, prompt_context_string):
    try:
        return gri.run_guardrails(answer_text, retrieved_chunks)
    except TypeError:
        return gri.run_guardrails(answer_text, retrieved_chunks, prompt_context_string)


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
    original_flag = gri.ENABLE_V2_SEMANTIC_SUPPORT_CHECK
    try:
        gri.ENABLE_V2_SEMANTIC_SUPPORT_CHECK = flag
        result = _call_guardrails(ANSWER, RETRIEVED_CHUNKS, CONTEXT)
    finally:
        gri.ENABLE_V2_SEMANTIC_SUPPORT_CHECK = original_flag
    outcome = (result or {}).get("status", "")
    reasons = _normalize_reasons(result)
    return outcome, reasons


ANSWER = "Alpha is first and blue [C1]. Beta is second and red [C2]."
CONTEXT = (
    "[C1]\ntext: Alpha is first.\n\n"
    "[C2]\ntext: Beta is second."
)
RETRIEVED_CHUNKS = [
    {"id": "C1", "text": "Alpha is first."},
    {"id": "C2", "text": "Beta is second."},
]


def main():
    outcome, reasons = run(False)
    print(f"[V2 OFF] outcome={outcome} reasons={reasons}")
    assert outcome == "PASS"

    outcome, reasons = run(True)
    print(f"[V2 ON ] outcome={outcome} reasons={reasons}")
    assert outcome == "WARN"
    assert "SEMANTIC_SUPPORT_WEAK" in reasons


if __name__ == "__main__":
    main()
