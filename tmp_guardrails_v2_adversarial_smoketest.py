"""
Guardrails v2.1 adversarial smoketest.
Validates WARN-only handling for spoofed citations, prompt injection, and hidden unsupported claims.
"""
import sys

from tmp_rag_guardrails_impl import run_guardrails


def _call_guardrails(answer_text, retrieved_chunks, prompt_context_string, **flags):
    try:
        return run_guardrails(answer_text, retrieved_chunks, prompt_context_string, **flags)
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


def _run_case(label, answer_text, retrieved_chunks, prompt_context_string, **flags):
    result = _call_guardrails(answer_text, retrieved_chunks, prompt_context_string, **flags)
    outcome = (result or {}).get("status", "")
    reasons = _normalize_reasons(result)
    print(f"[{label}] outcome={outcome} reasons={reasons}")
    return outcome, reasons


def main():
    all_ok = True

    # 1) Citation spoofing: cited ID absent from prompt context, but chunk exists.
    answer_text = "A is true [C1]. B is true [C2]. C is true [C3]. D is true [C4]. Uptime is 95% [C9]."
    retrieved_chunks = [
        {"id": "C1", "text": "A is true."},
        {"id": "C2", "text": "B is true."},
        {"id": "C3", "text": "C is true."},
        {"id": "C4", "text": "D is true."},
        {"id": "C9", "text": "Uptime is 90%."},
    ]
    prompt_context_string = (
        "[C1]\ntext: A is true.\n\n"
        "[C2]\ntext: B is true.\n\n"
        "[C3]\ntext: C is true.\n\n"
        "[C4]\ntext: D is true.\n\n"
        "[C9]\ntext: Uptime is 90%."
    )
    outcome, _reasons = _run_case(
        "SPOOFING",
        answer_text,
        retrieved_chunks,
        prompt_context_string,
        enable_v2_strict_claim_extraction=True,
        enable_v2_claim_citation_alignment=True,
        enable_v2_semantic_support_check=True,
    )
    all_ok &= outcome == "WARN" and outcome != "REFUSE"

    # 2) Prompt injection attempt: override citation rules inside answer text.
    answer_text = "Uptime is 99% [C1]."
    retrieved_chunks = [{"id": "C1", "text": "Uptime is 98%."}]
    prompt_context_string = "[C1]\ntext: Uptime is 98%."
    outcome, _reasons = _run_case(
        "INJECTION",
        answer_text,
        retrieved_chunks,
        prompt_context_string,
        enable_v2_semantic_support_check=True,
    )
    all_ok &= outcome == "WARN" and outcome != "REFUSE"

    # 3) Hidden unsupported claim: supported + unsupported numeric claim mix.
    answer_text = "Uptime is 95% [C1]. Warranty lasts 2 years [C2]."
    retrieved_chunks = [
        {"id": "C1", "text": "Uptime is 95%."},
        {"id": "C2", "text": "Warranty lasts 1 year."},
    ]
    prompt_context_string = "[C1]\ntext: Uptime is 95%.\n\n[C2]\ntext: Warranty lasts 1 year."
    outcome, _reasons = _run_case(
        "HIDDEN_UNSUPPORTED",
        answer_text,
        retrieved_chunks,
        prompt_context_string,
        enable_v2_claim_citation_alignment=True,
    )
    all_ok &= outcome == "WARN" and outcome != "REFUSE"

    # 4) Citation ID not in prompt context.
    answer_text = "Policy uptime is 96% [C1]."
    retrieved_chunks = [{"id": "C1", "text": "Policy uptime is 95%."}]
    prompt_context_string = "[C2]\ntext: Unrelated."
    outcome, _reasons = _run_case(
        "MISSING_CONTEXT",
        answer_text,
        retrieved_chunks,
        prompt_context_string,
        enable_v2_strict_claim_extraction=True,
        enable_v2_claim_citation_alignment=True,
        enable_v2_semantic_support_check=True,
    )
    all_ok &= outcome == "WARN" and outcome != "REFUSE"

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
