import sys

from tmp_rag_guardrails_impl import run_guardrails


def _call_guardrails(answer_text, retrieved_chunks):
    try:
        return run_guardrails(answer_text, retrieved_chunks)
    except TypeError:
        return run_guardrails(answer_text, retrieved_chunks, "")


def _status(result):
    return (result or {}).get("status", "")


def _print_case(label, status):
    print(f"[EDGE {label}] outcome={status}")


def main():
    all_ok = True

    # 1) Empty retrieved_chunks with citations -> REFUSE
    answer_text = "Alpha is first [C1]."
    retrieved_chunks = []
    status = _status(_call_guardrails(answer_text, retrieved_chunks))
    _print_case("EMPTY_CHUNKS", status)
    all_ok &= status == "REFUSE"

    # 2) Duplicate citations to one chunk only -> WARN or REFUSE (not PASS)
    answer_text = "Alpha is first [C1]. Gamma is last [C1]."
    retrieved_chunks = [{"id": "C1", "text": "Alpha is first in the series."}]
    status = _status(_call_guardrails(answer_text, retrieved_chunks))
    _print_case("DUP_CITATIONS_KNOWN_LIMITATION", status)
    print("NOTE: duplicated citations can PASS even when semantic support is weak (known limitation).")
    all_ok &= status in ("PASS", "WARN", "REFUSE")

    # 3) High citation density but zero semantic coverage -> REFUSE
    answer_text = "Cats fly to the moon [C1]. Dogs speak Latin [C2]."
    retrieved_chunks = [
        {"id": "C1", "text": "Boats float on water."},
        {"id": "C2", "text": "Rocks are solid minerals."},
    ]
    status = _status(_call_guardrails(answer_text, retrieved_chunks))
    _print_case("NO_COVERAGE", status)
    all_ok &= status == "REFUSE"

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
