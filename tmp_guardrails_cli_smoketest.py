import sys

import tmp_llm_answer_generator as runner


def _run_case(label, answer_text, retrieved_chunks, expected_exit_code):
    async def _stub_generate_answer_real(_prompt_payload):
        return answer_text

    runner.generate_answer_real = _stub_generate_answer_real

    prompt_payload = {
        "system_instruction": "Answer only using the provided context.",
        "instructions": "Cite sources like [C1].",
        "context": "stub context",
        "user_query": "stub question",
        "retrieved_chunks": retrieved_chunks,
    }

    exit_code = 0
    try:
        runner.generate_answer(prompt_payload, real=True)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            exit_code = exc.code
        else:
            exit_code = 1

    print(f"[CLI {label}] exit_code={exit_code}")
    return exit_code == expected_exit_code


def main():
    all_ok = True

    # PASS
    answer_text = "Alpha is first [C1]. Beta follows alpha [C2]."
    retrieved_chunks = [
        {"id": "C1", "text": "Alpha is first in the series."},
        {"id": "C2", "text": "Beta follows alpha in the sequence."},
    ]
    all_ok &= _run_case("PASS", answer_text, retrieved_chunks, 0)

    # WARN
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
    all_ok &= _run_case("WARN", answer_text, retrieved_chunks, 0)

    # REFUSE
    answer_text = "All data is accurate and complete."
    retrieved_chunks = []
    all_ok &= _run_case("REFUSE", answer_text, retrieved_chunks, 2)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
