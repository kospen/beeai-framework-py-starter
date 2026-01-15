import sys

from tmp_rag_guardrails_impl import run_guardrails


def _call_guardrails(answer_text, retrieved_chunks):
    try:
        return run_guardrails(answer_text, retrieved_chunks)
    except TypeError:
        return run_guardrails(answer_text, retrieved_chunks, "")


def _coerce_reasons(reasons_raw):
    if reasons_raw is None:
        return []
    if isinstance(reasons_raw, list):
        reasons = []
        for item in reasons_raw:
            if isinstance(item, str):
                reasons.append(item)
            elif isinstance(item, dict):
                reasons.append(item.get("message") or item.get("code") or str(item))
            else:
                reasons.append(str(item))
        return reasons
    if isinstance(reasons_raw, dict):
        return [reasons_raw.get("message") or reasons_raw.get("code") or str(reasons_raw)]
    return [str(reasons_raw)]


def normalize_result(value):
    outcome = None
    reasons_raw = None

    if isinstance(value, tuple):
        if len(value) > 0:
            outcome = value[0]
        if len(value) > 1:
            reasons_raw = value[1]
    elif isinstance(value, dict):
        outcome = value.get("status") or value.get("outcome")
        reasons_raw = value.get("reasons")
    else:
        outcome = getattr(value, "status", None) or getattr(value, "outcome", None)
        reasons_raw = getattr(value, "reasons", None)

    reasons = _coerce_reasons(reasons_raw)
    return {"outcome": str(outcome) if outcome is not None else "", "reasons": reasons}


def _is_informational(reasons):
    return all("info" in reason.lower() for reason in reasons)


def _assert(test_name, condition, message):
    if condition:
        return True
    print(f"[FAIL] {test_name}: {message}")
    return False


def main():
    passed_tests = 0

    # A_PASS
    answer_text = "Alpha is first [C1]. Beta follows alpha [C2]."
    retrieved_chunks = [
        {"id": "C1", "text": "Alpha is first in the series."},
        {"id": "C2", "text": "Beta follows alpha in the sequence."},
    ]
    result = normalize_result(_call_guardrails(answer_text, retrieved_chunks))
    print(f"[PASS TEST] outcome={result['outcome']} reasons={len(result['reasons'])}")
    section_ok = True
    section_ok &= _assert("PASS", result["outcome"] == "PASS", "expected outcome PASS")
    section_ok &= _assert(
        "PASS",
        not result["reasons"] or _is_informational(result["reasons"]),
        "expected no reasons or only informational reasons",
    )
    if section_ok:
        passed_tests += 1

    # B_WARN
    answer_text = (
        "The project timeline is approved [C1]. "
        "The budget matches the project scope [C1]. "
        "The team delivered the milestone on schedule [C2]. "
        "Stakeholders reviewed the timeline and scope. "
        "The office moved to Mars."
    )
    retrieved_chunks = [
        {"id": "C1", "text": "Project timeline budget scope approved."},
        {"id": "C2", "text": "Team delivered milestone on schedule."},
    ]
    result = normalize_result(_call_guardrails(answer_text, retrieved_chunks))
    print(f"[WARN TEST] outcome={result['outcome']} reasons={len(result['reasons'])}")
    section_ok = True
    section_ok &= _assert("WARN", result["outcome"] == "WARN", "expected outcome WARN")
    section_ok &= _assert("WARN", len(result["reasons"]) >= 1, "expected at least one reason")
    if section_ok:
        passed_tests += 1

    # C_REFUSE
    answer_text = "All data is accurate and complete."
    retrieved_chunks = []
    refused_exit_code = None
    result_value = None
    try:
        result_value = _call_guardrails(answer_text, retrieved_chunks)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            refused_exit_code = exc.code
        if isinstance(exc.code, (dict, tuple)):
            result_value = exc.code
    result = normalize_result(result_value)
    exit_code_label = "n/a" if refused_exit_code is None else str(refused_exit_code)
    print(f"[REFUSE TEST] outcome={result['outcome']} reasons={len(result['reasons'])} exit_code={exit_code_label}")
    section_ok = True
    section_ok &= _assert("REFUSE", result["outcome"] == "REFUSE", "expected outcome REFUSE")
    if refused_exit_code is not None:
        section_ok &= _assert("REFUSE", refused_exit_code == 2, "expected exit code 2")
    section_ok &= _assert("REFUSE", len(result["reasons"]) >= 1, "expected at least one reason")
    if section_ok:
        passed_tests += 1

    if passed_tests == 3:
        print("[OK] guardrails smoketest: 3/3 passed")
        sys.exit(0)
    print(f"[ERROR] guardrails smoketest: {passed_tests}/3 passed")
    sys.exit(1)


if __name__ == "__main__":
    main()
