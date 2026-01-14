import json
from dataclasses import dataclass, asdict
from typing import Any
import sys

@dataclass
class PlannedQuery:
    """Represents a planned RAG query with metadata."""
    query_text: str
    filters: dict[str, Any]
    topk: int


def plan_query(user_input: str) -> PlannedQuery:
    """
    Plan a RAG query from user input.
    
    Args:
        user_input: The raw user query string
        
    Returns:
        PlannedQuery with planning details
    """
    return PlannedQuery(
        query_text=user_input,
        filters={},
        topk=5
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tmp_rag_query_planner.py '<query>'")
        sys.exit(1)
    
    user_query = sys.argv[1]
    planned = plan_query(user_query)
    
    print(json.dumps(asdict(planned), indent=2))