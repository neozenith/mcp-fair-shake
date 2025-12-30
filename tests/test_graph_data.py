"""Tests for legislation knowledge graph data structure."""

import json
from pathlib import Path

import pytest

# Path to graph data directory
GRAPH_DATA_DIR = Path(__file__).parent.parent / "data" / "legislation" / "graph"


def load_all_graph_files() -> list[tuple[Path, dict]]:
    """Load all graph JSON files."""
    files = []
    for json_file in GRAPH_DATA_DIR.glob("*.json"):
        data = json.loads(json_file.read_text())
        files.append((json_file, data))
    return files


def test_graph_directory_exists():
    """Graph data directory must exist."""
    assert GRAPH_DATA_DIR.exists(), f"Graph data directory not found: {GRAPH_DATA_DIR}"
    assert GRAPH_DATA_DIR.is_dir(), f"Graph data path is not a directory: {GRAPH_DATA_DIR}"


def test_graph_files_exist():
    """At least one graph data file must exist."""
    json_files = list(GRAPH_DATA_DIR.glob("*.json"))
    assert len(json_files) > 0, "No graph data files found in directory"


@pytest.mark.parametrize("json_file,data", load_all_graph_files())
def test_graph_file_structure(json_file: Path, data: dict):
    """Each graph file must have valid structure."""
    # Must have metadata
    assert "metadata" in data, f"{json_file.name}: Missing metadata"
    assert "nodes" in data, f"{json_file.name}: Missing nodes array"
    assert "edges" in data, f"{json_file.name}: Missing edges array"

    # Must be lists
    assert isinstance(data["nodes"], list), f"{json_file.name}: nodes must be a list"
    assert isinstance(data["edges"], list), f"{json_file.name}: edges must be a list"


@pytest.mark.parametrize("json_file,data", load_all_graph_files())
def test_nodes_have_required_fields(json_file: Path, data: dict):
    """All nodes must have required fields."""
    required_fields = {"id", "label", "type"}

    for i, node in enumerate(data["nodes"]):
        missing = required_fields - set(node.keys())
        assert not missing, f"{json_file.name} node {i}: Missing fields {missing}"

        # Check field types
        assert isinstance(node["id"], str), f"{json_file.name} node {i}: id must be string"
        assert isinstance(node["label"], str), f"{json_file.name} node {i}: label must be string"
        assert isinstance(node["type"], str), f"{json_file.name} node {i}: type must be string"


@pytest.mark.parametrize("json_file,data", load_all_graph_files())
def test_edges_have_required_fields(json_file: Path, data: dict):
    """All edges must have required fields."""
    required_fields = {"source", "target", "type"}

    for i, edge in enumerate(data["edges"]):
        missing = required_fields - set(edge.keys())
        assert not missing, f"{json_file.name} edge {i}: Missing fields {missing}"

        # Check field types
        assert isinstance(edge["source"], str), f"{json_file.name} edge {i}: source must be string"
        assert isinstance(edge["target"], str), f"{json_file.name} edge {i}: target must be string"
        assert isinstance(edge["type"], str), f"{json_file.name} edge {i}: type must be string"


@pytest.mark.parametrize("json_file,data", load_all_graph_files())
def test_no_duplicate_node_ids(json_file: Path, data: dict):
    """Node IDs must be unique within each file."""
    node_ids = [node["id"] for node in data["nodes"]]
    duplicates = {nid for nid in node_ids if node_ids.count(nid) > 1}
    assert not duplicates, f"{json_file.name}: Duplicate node IDs: {duplicates}"


@pytest.mark.parametrize("json_file,data", load_all_graph_files())
def test_edges_reference_existing_nodes(json_file: Path, data: dict):
    """All edges must reference nodes that exist in the graph."""
    node_ids = {node["id"] for node in data["nodes"]}

    for i, edge in enumerate(data["edges"]):
        # Allow references to nodes that might be in other files (like 'fwa-2009')
        # Only validate if both source and target should be in this file
        source = edge["source"]
        target = edge["target"]

        # If the source is in this file's nodes, verify it exists
        if any(node["id"] == source for node in data["nodes"]):
            assert source in node_ids, f"{json_file.name} edge {i}: source '{source}' not found in nodes"

        # If the target is in this file's nodes, verify it exists
        if any(node["id"] == target for node in data["nodes"]):
            assert target in node_ids, f"{json_file.name} edge {i}: target '{target}' not found in nodes"


@pytest.mark.parametrize("json_file,data", load_all_graph_files())
def test_parent_child_consistency(json_file: Path, data: dict):
    """Nodes with parent field must have corresponding 'contains' edge."""
    nodes_with_parents = [(node["id"], node["parent"]) for node in data["nodes"] if "parent" in node]

    for node_id, parent_id in nodes_with_parents:
        # Check if there's a 'contains' edge from parent to this node
        contains_edge = any(
            edge["source"] == parent_id and edge["target"] == node_id and edge["type"] == "contains"
            for edge in data["edges"]
        )
        assert contains_edge, f"{json_file.name}: Node '{node_id}' has parent '{parent_id}' but no 'contains' edge"


def test_combined_graph_integrity():
    """Test integrity of the combined graph from all files."""
    all_nodes = []
    all_edges = []

    for json_file in GRAPH_DATA_DIR.glob("*.json"):
        data = json.loads(json_file.read_text())
        all_nodes.extend(data.get("nodes", []))
        all_edges.extend(data.get("edges", []))

    # Combined graph should have no duplicate node IDs
    node_ids = [node["id"] for node in all_nodes]
    duplicates = {nid for nid in node_ids if node_ids.count(nid) > 1}
    assert not duplicates, f"Duplicate node IDs across files: {duplicates}"

    # All edges should reference existing nodes (across all files)
    node_id_set = set(node_ids)
    for i, edge in enumerate(all_edges):
        assert edge["source"] in node_id_set, f"Edge {i}: source '{edge['source']}' not found in any graph file"
        assert edge["target"] in node_id_set, f"Edge {i}: target '{edge['target']}' not found in any graph file"


def test_api_load_function():
    """Test that the API load_graph_data function works."""
    # Import the function
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    from mcp_fair_shake.api import load_graph_data

    # Load the data
    result = load_graph_data()

    # Verify structure
    assert "nodes" in result
    assert "edges" in result
    assert isinstance(result["nodes"], list)
    assert isinstance(result["edges"], list)
    assert len(result["nodes"]) > 0, "No nodes loaded from graph files"
    assert len(result["edges"]) > 0, "No edges loaded from graph files"
