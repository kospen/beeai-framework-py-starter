import asyncio
import sys
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from beeai_framework.adapters.gemini.backend.embedding import GeminiEmbeddingModel
from tmp_rag_query_planner import plan_query

async def main_async():
    if len(sys.argv) < 2:
        print("Usage: python tmp_rag_query_run.py '<query>'")
        sys.exit(1)
    
    user_input = sys.argv[1]
    
    # Plan the query
    planned = plan_query(user_input)
    print(f"Planned Query:")
    print(f"  query_text: {planned.query_text}")
    print(f"  filters: {planned.filters}")
    print(f"  topk: {planned.topk}")
    print()
    
    # Create Gemini embedding
    model = GeminiEmbeddingModel(model_id="text-embedding-004")
    run = model.create([planned.query_text])
    result = await run.handler()
    embedding = result.embeddings[0]
    
    # Build Qdrant filter
    query_filter = None
    if planned.filters:
        conditions = []
        for field, value in planned.filters.items():
            conditions.append(
                qm.FieldCondition(
                    key=field,
                    match=qm.MatchValue(value=value)
                )
            )
        query_filter = qm.Filter(must=conditions)
    
    # Query Qdrant
    client = QdrantClient(url="http://localhost:6333")
    try:
        results = client.query_points(
            collection_name="belbin_rag_v1",
            query=embedding,
            query_filter=query_filter,
            limit=planned.topk
        )
        
        # Print results
        print("Results:")
        for point in results.points:
            payload = point.payload
            snippet = payload.get("text", "")[:200]
            print(f"  Score: {point.score}")
            print(f"  Source: {payload.get('source_file')}")
            print(f"  Type: {payload.get('type')}")
            print(f"  Topic: {payload.get('topic')}")
            print(f"  Chunk Index: {payload.get('chunk_index')}")
            print(f"  Snippet: {snippet}")
            print()
    except Exception as e:
        print(f"Error querying Qdrant: {e}")


if __name__ == "__main__":
    asyncio.run(main_async())
