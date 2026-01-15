import argparse
import asyncio
import os
import sys

from beeai_framework.errors import FrameworkError
from tmp_rag_guardrails_impl import run_guardrails


def _env_truthy(name: str) -> bool:
    value = os.getenv(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


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


async def generate_answer_real(prompt_payload: dict) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set in the environment.")
        sys.exit(1)

    prompt = build_llm_prompt(prompt_payload)

    model_id = "gemini-2.5-flash"
    try:
        from belbin_engine.utils.provider_loader import load_provider_profile

        profile = load_provider_profile()
        gemini_cfg = profile.get("providers", {}).get("gemini", {}).get("llm", {})
        model_id = gemini_cfg.get("model_id", model_id)
    except Exception:
        pass

    from beeai_framework.backend import ChatModel, UserMessage

    llm = ChatModel.from_name("gemini:gemini-2.5-flash")
    run = llm.run([UserMessage(prompt)])
    try:
        out = await run.handler()
    except FrameworkError as e:
        print(e.explain())
        sys.exit(1)

    # Extract assistant text
    if hasattr(out, "output") and out.output:
        msg = out.output[-1]
        if hasattr(msg, "content"):
            content = msg.content

            # If content is a list of MessageTextContent-like items
            if isinstance(content, list) and content:
                first = content[0]
                if hasattr(first, "text") and first.text:
                    return first.text

            # If content is already a string
            if isinstance(content, str):
                return content

            # Fallback
            return str(content)
        if hasattr(msg, "text"):
            return msg.text

    return str(out)

    message = getattr(out, "message", None)
    content = getattr(message, "content", None) if message else None
    if isinstance(content, str) and content.strip():
        return content

    messages = getattr(out, "messages", None)
    if messages:
        last = messages[-1]
        last_content = getattr(last, "content", None)
        if isinstance(last_content, str) and last_content.strip():
            return last_content

    text = getattr(out, "text", None)
    if isinstance(text, str) and text.strip():
        return text

    return str(out)


def generate_answer(prompt_payload: dict, real: bool = False) -> str:
    _ = build_llm_prompt(prompt_payload)
    if not real:
        return "LLM ANSWER (stub): this is where the model response will go."
    answer_text = asyncio.run(generate_answer_real(prompt_payload))
    # Guardrails v2 flags are opt-in and default OFF.
    guardrails_result = run_guardrails(
        answer_text=answer_text,
        retrieved_chunks=prompt_payload.get("retrieved_chunks", []),
        prompt_context_string=prompt_payload.get("context", ""),
        enable_v2_semantic_support_check=_env_truthy("ENABLE_V2_SEMANTIC_SUPPORT_CHECK"),
        enable_v2_strict_claim_extraction=_env_truthy("ENABLE_V2_STRICT_CLAIM_EXTRACTION"),
        enable_v2_claim_citation_alignment=_env_truthy("ENABLE_V2_CLAIM_CITATION_ALIGNMENT"),
    )

    status = guardrails_result.get("status")
    reasons = guardrails_result.get("reasons", []) or []
    reason_lines = [f"{r.get('code')}: {r.get('message')}" for r in reasons]

    if status == "REFUSE":
        print("REFUSED: answer not supported by retrieval context")
        if reason_lines:
            print("\n".join(reason_lines))
        sys.exit(2)

    if status == "WARN":
        warning_lines = ["WARNING: guardrails partial coverage"]
        if reason_lines:
            warning_lines.extend(reason_lines)
        warning_lines.append(answer_text)
        return "\n".join(warning_lines)

    return answer_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Answer Generator (stub or Gemini).")
    parser.add_argument("--real", action="store_true", help="Call Gemini via beeai_framework.")
    args = parser.parse_args()

    example_payload = {
        "system_instruction": "Answer only using the provided context.",
        "instructions": "Cite sources like [C1].",
        "context": "[C1]\nsource_file: docs/example.md\ntext: Example context text.",
        "user_query": "What is the example about?",
    }

    combined_prompt = build_llm_prompt(example_payload)
    print(combined_prompt)
    print()
    print(generate_answer(example_payload, real=args.real))
