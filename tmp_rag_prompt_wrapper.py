import json


def build_prompt(user_query: str, retrieved_chunks: list[dict]) -> dict:
    system_instruction = (
        "You are a helpful assistant. Answer ONLY using the provided context. "
        "If the answer is not in the context, say you do not know."
    )

    context_lines = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        label = f"[C{idx}]"
        source_file = chunk.get("source_file", "")
        chunk_type = chunk.get("type", "")
        topic = chunk.get("topic", "")
        chunk_index = chunk.get("chunk_index", "")
        text = chunk.get("text", "")

        context_lines.append(
            f"{label}\n"
            f"source_file: {source_file}\n"
            f"type/topic: {chunk_type} / {topic}\n"
            f"chunk_index: {chunk_index}\n"
            f"text: {text}"
        )

    context = "\n\n".join(context_lines)

    instructions = (
        "Cite sources using bracketed chunk labels like [C1]. "
        "If multiple chunks support a statement, cite all relevant chunks."
    )

    return {
        "system_instruction": system_instruction,
        "user_query": user_query,
        "context": context,
        "instructions": instructions,
    }


if __name__ == "__main__":
    example_query = "What is the recommended deployment strategy?"
    example_chunks = [
        {
            "score": 0.82,
            "source_file": "docs/deployment.md",
            "type": "guide",
            "topic": "deployment",
            "chunk_index": 3,
            "text": "Use blue-green deployments to reduce downtime and risk.",
        },
        {
            "score": 0.74,
            "source_file": "docs/operations.md",
            "type": "handbook",
            "topic": "operations",
            "chunk_index": 11,
            "text": "Monitor error rates during rollout and be ready to roll back.",
        },
    ]

    payload = build_prompt(example_query, example_chunks)
    print(json.dumps(payload, indent=2))
