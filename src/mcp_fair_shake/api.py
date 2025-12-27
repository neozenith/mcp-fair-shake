"""FastAPI server for legislation knowledge graph visualization."""

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


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "message": "MCP Fair Shake API is running"}


@app.get("/api/graph")
async def get_graph() -> dict[str, list]:
    """Get the legislation knowledge graph.

    Returns a minimal placeholder graph structure.
    """
    return {
        "nodes": [
            {"id": "fwa-2009", "label": "Fair Work Act 2009", "type": "act"},
            {"id": "fwa-s394", "label": "Section 394", "type": "section"},
        ],
        "edges": [
            {"source": "fwa-2009", "target": "fwa-s394", "type": "contains"},
        ],
    }
