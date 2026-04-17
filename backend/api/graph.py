"""
Graph API routes.
GET /graph/nodes — returns graph node list.
GET /graph/edges — returns graph edge list.
GET /node/{node_id}/state — returns before/after state of a node.
"""

from fastapi import APIRouter, HTTPException

from schemas.response_models import (
    GraphNodesResponse,
    GraphEdgesResponse,
    GraphNode,
    GraphEdge,
    NodeStateResponse,
)
from graph.crag_graph import GRAPH_NODES, GRAPH_EDGES, get_node_states

router = APIRouter()


@router.get("/graph/nodes", response_model=GraphNodesResponse)
def get_graph_nodes():
    """Return the list of nodes in the CRAG graph."""
    nodes = [GraphNode(**n) for n in GRAPH_NODES]
    return GraphNodesResponse(nodes=nodes)


@router.get("/graph/edges", response_model=GraphEdgesResponse)
def get_graph_edges():
    """Return the list of edges in the CRAG graph."""
    edges = [GraphEdge(**e) for e in GRAPH_EDGES]
    return GraphEdgesResponse(edges=edges)


@router.get("/node/{node_id}/state", response_model=NodeStateResponse)
def get_node_state(node_id: str):
    """
    Return the before and after state of a specific node
    from the most recent pipeline run.
    """
    node_states = get_node_states()

    if node_id not in node_states:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{node_id}' not found. Either it wasn't executed in the last run or no query has been made yet."
        )

    return NodeStateResponse(
        node_id=node_id,
        input_state=node_states[node_id]["input_state"],
        output_state=node_states[node_id]["output_state"],
    )
