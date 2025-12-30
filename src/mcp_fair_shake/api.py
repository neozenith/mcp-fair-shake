"""FastAPI server for legislation knowledge graph visualization."""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MCP Fair Shake API",
    description="Australian Workplace Legislation Knowledge Graph API",
    version="0.1.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5273", "http://localhost:5274"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to graph data directory
GRAPH_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "legislation" / "graph"


def load_graph_data() -> dict[str, list]:
    """Load legislation knowledge graph from JSON files.

    Returns:
        Dictionary with 'nodes' and 'edges' lists containing all graph data.
    """
    all_nodes: list[dict] = []
    all_edges: list[dict] = []

    # Load all JSON files from graph directory
    for json_file in GRAPH_DATA_DIR.glob("*.json"):
        try:
            data = json.loads(json_file.read_text())
            all_nodes.extend(data.get("nodes", []))
            all_edges.extend(data.get("edges", []))
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to load {json_file}: {e}")
            continue

    return {"nodes": all_nodes, "edges": all_edges}


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "message": "MCP Fair Shake API is running"}


@app.get("/api/graph")
async def get_graph() -> dict[str, list]:
    """Get the legislation knowledge graph.

    Loads graph data from JSON files in data/legislation/graph/ directory.
    Returns comprehensive graph of all in-scope Australian workplace legislation.
    """
    return load_graph_data()
