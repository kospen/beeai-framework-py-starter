import sys

import tmp_rag_guardrails_impl as gri


def _call_guardrails(answer_text, retrieved_chunks):
    try:
        return gri.run_guardrails(answer_text, retrieved_chunks)
    except TypeError:
        return gri.run_guardrails(answer_text, retrieved_chunks, "")


def _outcome(result):
    return (result or {}).get("status", "")


def _has_reason_code(result, code):
    for reason in (result or {}).get("reasons", []) or []:
        if isinstance(reason, dict) and reason.get("code") == code:
            return True
    return False


def main():
    all_ok = True

    answer_text = "Alpha is first [C1]. Alpha is first again [C1]. Alpha is first once more [C1]."
    retrieved_chunks = [{"id": "C1", "text": "Alpha is first in the series."}]

    result = _call_guardrails(answer_text, retrieved_chunks)
    outcome = _outcome(result)
    print(f"[V2 OFF] outcome={outcome}")
    all_ok &= outcome == "PASS"

    original_flag = gri.ENABLE_V2_CITATION_DEDUP_PENALTY
    try:
        gri.ENABLE_V2_CITATION_DEDUP_PENALTY = True
        result = _call_guardrails(answer_text, retrieved_chunks)
    finally:
        gri.ENABLE_V2_CITATION_DEDUP_PENALTY = original_flag

    outcome = _outcome(result)
    print(f"[V2 ON] outcome={outcome}")
    all_ok &= outcome == "WARN"
    all_ok &= _has_reason_code(result, "CITATION_DEDUP_DOMINANCE")

    if all_ok:
        print("[OK] guardrails v2 flags smoketest: 2/2 passed")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
