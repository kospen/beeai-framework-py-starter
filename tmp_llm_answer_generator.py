def build_llm_prompt(prompt_payload: dict) -> str:
    system_instruction = prompt_payload.get("system_instruction", "")
    instructions = prompt_payload.get("instructions", "")
    context = prompt_payload.get("context", "")
    user_query = prompt_payload.get("user_query", "")

    parts = [
        "SYSTEM INSTRUCTION",
        system_instruction,
        "",
        "INSTRUCTIONS",
        instructions,
        "",
        "CONTEXT",
        context,
        "",
        f"User question: {user_query}",
    ]
    return "\n".join(parts)


def generate_answer(prompt_payload: dict) -> str:
    _ = build_llm_prompt(prompt_payload)
    return "LLM ANSWER (stub): this is where the model response will go."


if __name__ == "__main__":
    example_payload = {
        "system_instruction": "Answer only using the provided context.",
        "instructions": "Cite sources like [C1].",
        "context": "[C1]\nsource_file: docs/example.md\ntext: Example context text.",
        "user_query": "What is the example about?",
    }

    combined_prompt = build_llm_prompt(example_payload)
    print(combined_prompt)
    print()
    print(generate_answer(example_payload))
