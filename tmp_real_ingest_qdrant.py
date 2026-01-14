import argparse
import asyncio
import hashlib
import json
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from beeai_framework.adapters.gemini.backend.embedding import GeminiEmbeddingModel
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

# paths
INGEST_DIR = Path("belbin_engine_data/ingest/seed")
CONFIG_PATH = Path("belbin_engine_data/ingest/ingest_config.json")

EXPECTED_DIM = 768
MODEL_ID = "text-embedding-004"


def chunk_text(text: str, max_chars: int, overlap: int) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def load_config() -> Dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing ingest config: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def resolve_file_rules(cfg: Dict) -> List[Dict]:
    return cfg.get("file_rules", [])


def match_file_rule(filename: str, rules: List[Dict]) -> Tuple[str, str]:
    for rule in rules:
        if rule.get("pattern") == filename:
            return rule.get("type", "UNKNOWN"), rule.get("topic", "UNKNOWN")
    return "UNKNOWN", "UNKNOWN"


def stable_point_id(filename: str, chunk_index: int, text: str) -> str:
    raw = f"{filename}|{chunk_index}|{text}".encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()
    return str(uuid.UUID(h[:32]))


async def embed_text(model: GeminiEmbeddingModel, text: str) -> List[float]:
    run = model.create([text])
    out = await run.handler()  # handler itself is a coroutine returning the output
    vec = out.embeddings[0]
    if len(vec) != EXPECTED_DIM:
        raise ValueError(f"Embedding dim mismatch: expected {EXPECTED_DIM}, got {len(vec)}")
    return vec


async def main_async() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingest", action="store_true")
    parser.add_argument("--query", default="Belbin Orchestra decision loop")
    parser.add_argument("--topk", type=int, default=5)
    parser.add_argument("--type")
    parser.add_argument("--topic")
    parser.add_argument("--source_file")
    parser.add_argument("--count_only", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    collection = cfg.get("collection")
    if not collection:
        raise ValueError("Missing 'collection' in ingest config")

    chunking = cfg.get("chunking", {})
    max_chars = chunking.get("max_chars")
    overlap = chunking.get("overlap")
    if max_chars is None or overlap is None:
        raise ValueError("Missing chunking.max_chars or chunking.overlap in ingest config")

    metadata_defaults = cfg.get("metadata_defaults", {})
    source_type = metadata_defaults.get("source_type", "UNKNOWN")
    language = metadata_defaults.get("language", "UNKNOWN")

    rules = resolve_file_rules(cfg)

    client = QdrantClient(url="http://localhost:6333")

    total_chunks = 0
    total_points = 0

    print("REAL INGEST -> QDRANT")
    print(f"collection: {collection}")
    print(f"ingest: {args.ingest}")
    print("")

    conditions = []
    if args.type:
        conditions.append(
            qm.FieldCondition(key="type", match=qm.MatchValue(value=args.type))
        )
    if args.topic:
        conditions.append(
            qm.FieldCondition(key="topic", match=qm.MatchValue(value=args.topic))
        )
    if args.source_file:
        conditions.append(
            qm.FieldCondition(
                key="source_file", match=qm.MatchValue(value=args.source_file)
            )
        )

    if args.count_only and not conditions:
        print(
            "ERROR: --count_only requires at least one filter (--type, --topic, or --source_file)"
        )
        raise SystemExit(1)

    if args.count_only:
        query_filter = qm.Filter(must=conditions) if conditions else None
        count_res = client.count(
            collection_name=collection,
            count_filter=query_filter,
            exact=True,
        )
        print("COUNT:", count_res.count)
        return

    embedding_model = GeminiEmbeddingModel(model_id=MODEL_ID)

    if args.ingest:
        if not INGEST_DIR.exists():
            raise FileNotFoundError(f"Missing ingest seed directory: {INGEST_DIR}")

        files = sorted(INGEST_DIR.glob("*.md"))
        if not files:
            raise FileNotFoundError(f"No .md files found in {INGEST_DIR}")

        print(f"files: {len(files)}")
        print("")

        for p in files:
            text = p.read_text(encoding="utf-8")
            chunks = chunk_text(text, max_chars, overlap)
            file_type, topic = match_file_rule(p.name, rules)

            points: List[qm.PointStruct] = []
            for idx, chunk in enumerate(chunks):
                vec = await embed_text(embedding_model, chunk)
                payload = {
                    "type": file_type,
                    "topic": topic,
                    "source_file": p.name,
                    "chunk_index": idx,
                    "source_type": source_type,
                    "language": language,
                    "text": chunk,
                }
                point_id = stable_point_id(p.name, idx, chunk)
                points.append(qm.PointStruct(id=point_id, vector=vec, payload=payload))

            if points:
                client.upsert(collection_name=collection, points=points)

            total_chunks += len(chunks)
            total_points += len(points)
            print(f"- {p.name}: {len(chunks)} chunks")

        print("")
        print("SUMMARY")
        print("files:", len(files))
        print("total chunks:", total_chunks)
        print("upserted points:", total_points)
        print("")

    query_filter = qm.Filter(must=conditions) if conditions else None

    query_vec = await embed_text(embedding_model, args.query)
    res = client.query_points(
        collection_name=collection,
        query=query_vec,
        limit=args.topk,
        with_payload=True,
        query_filter=query_filter,
    )
    hits = res.points

    print("RETRIEVAL TEST")
    print("query:", args.query)
    print("topk:", args.topk)
    print("")
    for hit in hits:
        payload = hit.payload or {}
        snippet = (payload.get("text", "")[:200]).replace("\n", " ")
        print("score:", hit.score)
        print(
            "source_file:", payload.get("source_file"),
            "type:", payload.get("type"),
            "topic:", payload.get("topic"),
            "chunk_index:", payload.get("chunk_index"),
        )
        print("snippet:", snippet)
        print("")


def main() -> None:
    try:
        asyncio.run(main_async())
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise


if __name__ == "__main__":
    main()
