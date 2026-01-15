from typing import Any, Dict, List, Set


def _extract_citations(answer_text: str) -> List[str]:
    citations: List[str] = []
    seen: set[str] = set()
    i = 0
    text_len = len(answer_text)

    while i < text_len:
        if answer_text[i] == "[" and i + 2 < text_len and answer_text[i + 1] == "C":
            j = i + 2
            while j < text_len and answer_text[j].isdigit():
                j += 1
            if j > i + 2 and j < text_len and answer_text[j] == "]":
                cite_id = answer_text[i + 1 : j]
                if cite_id not in seen:
                    citations.append(cite_id)
                    seen.add(cite_id)
                i = j + 1
                continue
        i += 1

    return citations


def _split_into_claims(answer_text: str) -> List[str]:
    claims: List[str] = []
    buf: list[str] = []

    for ch in answer_text:
        if ch == "\n" or ch in ".?!":
            segment = "".join(buf).strip()
            if segment:
                claims.append(segment)
            buf = []
        else:
            buf.append(ch)

    tail = "".join(buf).strip()
    if tail:
        claims.append(tail)

    return claims


def _filter_non_claims(claims: List[str]) -> List[str]:
    filtered: List[str] = []
    prefixes = [
        "i cannot",
        "i can't",
        "cannot find",
        "not found in the context",
        "insufficient context",
        "i don't have",
        "i do not have",
        "as an ai",
        "i am an ai",
        "i canƒ?Tt",
    ]

    for claim in claims:
        stripped = claim.strip()
        if len(stripped) < 8:
            continue
        if not any(ch.isalnum() for ch in stripped):
            continue

        lowered = stripped.lower()
        if any(lowered.startswith(prefix) for prefix in prefixes):
            continue

        filtered.append(stripped)

    return filtered


def _build_chunk_lookup(retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for chunk in retrieved_chunks:
        chunk_id = chunk.get("id")
        if not chunk_id:
            chunk_index = chunk.get("chunk_index")
            if isinstance(chunk_index, int):
                chunk_id = f"C{chunk_index}"
        if isinstance(chunk_id, str) and chunk_id:
            lookup[chunk_id] = chunk
    return lookup


def _tokenize(text: str) -> Set[str]:
    tokens: List[str] = []
    buf: List[str] = []
    for ch in text.lower():
        if ch.isalnum():
            buf.append(ch)
        else:
            if buf:
                tokens.append("".join(buf))
                buf = []
    if buf:
        tokens.append("".join(buf))
    return set(tokens)


def _overlap_ratio(claim_tokens: Set[str], chunk_tokens: Set[str]) -> float:
    if not claim_tokens:
        return 0.0
    overlap = claim_tokens & chunk_tokens
    return len(overlap) / max(1, len(claim_tokens))
