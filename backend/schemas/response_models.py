"""
Response models for the API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class IngestResponse(BaseModel):
    """Response after ingesting a document."""
    status: str
    message: str
    num_chunks: int


class QueryResponse(BaseModel):
    """Response after running the CRAG pipeline."""
    answer: str
    verdict: str
    reason: str
    web_query: str
    num_good_docs: int
    num_kept_strips: int


class GraphNode(BaseModel):
    """A single node in the CRAG graph."""
    id: str
    label: str


class GraphEdge(BaseModel):
    """A single edge in the CRAG graph."""
    source: str
    target: str
    label: Optional[str] = None
    is_conditional: bool = False


class GraphNodesResponse(BaseModel):
    """List of graph nodes."""
    nodes: List[GraphNode]


class GraphEdgesResponse(BaseModel):
    """List of graph edges."""
    edges: List[GraphEdge]


class NodeStateResponse(BaseModel):
    """Before and after state of a node execution."""
    node_id: str
    input_state: Dict[str, Any]
    output_state: Dict[str, Any]
