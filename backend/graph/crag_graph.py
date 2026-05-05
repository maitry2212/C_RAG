"""
CRAG Graph Pipeline.
Exact logic from Notebook 4 — all nodes, edges, routing, prompts preserved.
"""

import os
import re
import copy
from typing import List, TypedDict, Dict, Any

from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langchain_community.tools.tavily_search import TavilySearchResults

from services.embedding import get_embedding_model
from services.vectorstore import query_vectors

load_dotenv()

# -------------------------------------------------------------------
# Configuration (same defaults as Notebook 4)
# -------------------------------------------------------------------
RET_LIMIT = 3
TAVILY_LIMIT = 1
UPPER_TH = 0.7
LOWER_TH = 0.3

# -------------------------------------------------------------------
# LLM (same as Notebook 4)
# -------------------------------------------------------------------
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.7
)

# -------------------------------------------------------------------
# State (exact TypedDict from Notebook 4)
# -------------------------------------------------------------------
class State(TypedDict):
    question: str
    user_id: int

    docs: List[Document]
    good_docs: List[Document]

    verdict: str
    reason: str

    strips: List[str]
    kept_strips: List[str]
    refined_context: str

    web_query: str

    web_docs: List[Document]

    answer: str


# -------------------------------------------------------------------
# Retrieve node
# -------------------------------------------------------------------
def retrieve_node(state: State) -> State:
    q = state["question"]
    emd_model = get_embedding_model()
    query_vector = emd_model.encode_query(q)

    from services.vectorstore import get_client
    client = get_client()
    collection_name = f"user_{state['user_id']}"
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=RET_LIMIT
    )
    return {"docs": [Document(page_content=p.payload["text"], metadata={"id": p.id}) for p in results.points]}


# -------------------------------------------------------------------
# Score-based doc evaluator (exact from Notebook 4)
# -------------------------------------------------------------------
class DocEvalScore(BaseModel):
    score: float
    reason: str


doc_eval_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a strict retrieval evaluator for RAG.\n"
            "You will be given ONE retrieved chunk and a question.\n"
            "Return a relevance score in [0.0, 1.0].\n"
            "- 1.0: chunk alone is sufficient to answer fully/mostly\n"
            "- 0.0: chunk is irrelevant\n"
            "Be conservative with high scores.\n"
            "Also return a short reason.\n"
            "Output JSON only.",
        ),
        ("human", "Question: {question}\n\nChunk:\n{chunk}"),
    ]
)

doc_eval_chain = doc_eval_prompt | llm.with_structured_output(DocEvalScore)


def eval_each_doc_node(state: State) -> State:
    q = state["question"]
    scores: List[float] = []
    good: List[Document] = []

    for d in state["docs"]:
        out = doc_eval_chain.invoke({"question": q, "chunk": d.page_content})
        scores.append(out.score)

        # Keep any doc above LOWER_TH as "weakly relevant"
        if out.score > LOWER_TH:
            good.append(d)

    # CORRECT: at least one doc > UPPER_TH
    if any(s > UPPER_TH for s in scores):
        return {
            "good_docs": good,
            "verdict": "CORRECT",
            "reason": f"At least one retrieved chunk scored > {UPPER_TH}.",
        }

    # INCORRECT: all docs < LOWER_TH
    if len(scores) > 0 and all(s < LOWER_TH for s in scores):
        return {
            "good_docs": [],
            "verdict": "INCORRECT",
            "reason": f"All retrieved chunks scored < {LOWER_TH}.",
        }

    # AMBIGUOUS: otherwise
    return {
        "good_docs": good,
        "verdict": "AMBIGUOUS",
        "reason": f"No chunk scored > {UPPER_TH}, but not all were < {LOWER_TH}.",
    }


# -------------------------------------------------------------------
# Sentence-level DECOMPOSER (exact from Notebook 4)
# -------------------------------------------------------------------
def decompose_to_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


# -------------------------------------------------------------------
# FILTER (LLM judge) — exact from Notebook 4
# -------------------------------------------------------------------
class KeepOrDrop(BaseModel):
    keep: bool = Field(description="Must be a boolean value (true or false), not a string.")


filter_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a strict relevance filter.\n"
            "Set `keep` to boolean true (not a string) only if the sentence directly helps answer the question.\n"
            "Use ONLY the sentence. Output JSON only.",
        ),
        ("human", "Question: {question}\n\nSentence:\n{sentence}"),
    ]
)

filter_chain = filter_prompt | llm.with_structured_output(KeepOrDrop)


# -------------------------------------------------------------------
# Knowledge refinement (exact from Notebook 4)
# -------------------------------------------------------------------
def refine(state: State) -> State:
    q = state["question"]

    if state.get("verdict") == "CORRECT":
        docs_to_use = state["good_docs"]
    elif state.get("verdict") == "INCORRECT":
        docs_to_use = state["web_docs"]
    else:  # AMBIGUOUS
        docs_to_use = state["good_docs"] + state["web_docs"]

    context = "\n\n".join(d.page_content for d in docs_to_use).strip()

    strips = decompose_to_sentences(context)

    kept: List[str] = []
    for s in strips:
        if filter_chain.invoke({"question": q, "sentence": s}).keep:
            kept.append(s)

    refined_context = "\n".join(kept).strip()

    return {
        "strips": strips,
        "kept_strips": kept,
        "refined_context": refined_context,
    }


# -------------------------------------------------------------------
# Query rewrite for web search (exact from Notebook 4)
# -------------------------------------------------------------------
class WebQuery(BaseModel):
    query: str


rewrite_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Rewrite the user question into a web search query composed of keywords.\n"
            "Rules:\n"
            "- Keep it short (6–14 words).\n"
            "- If the question implies recency (e.g., recent/latest/last week/last month), add a constraint like (last 30 days).\n"
            "- Do NOT answer the question.\n"
            "- Return JSON with a single key: query",
        ),
        ("human", "Question: {question}"),
    ]
)

rewrite_chain = rewrite_prompt | llm.with_structured_output(WebQuery)


def rewrite_query_node(state: State) -> State:
    out = rewrite_chain.invoke({"question": state["question"]})
    return {"web_query": out.query}


# -------------------------------------------------------------------
# Web search node (exact from Notebook 4)
# -------------------------------------------------------------------
tavily = TavilySearchResults(max_results=TAVILY_LIMIT)


def web_search_node(state: State) -> State:
    q = state.get("web_query") or state["question"]
    results = tavily.invoke({"query": q})

    web_docs: List[Document] = []
    for r in results or []:
        title = r.get("title", "")
        url = r.get("url", "")
        content = r.get("content", "") or r.get("snippet", "")
        text = f"TITLE: {title}\nURL: {url}\nCONTENT:\n{content}"
        web_docs.append(Document(page_content=text, metadata={"url": url, "title": title}))

    return {"web_docs": web_docs}


# -------------------------------------------------------------------
# Generate (exact from Notebook 4)
# -------------------------------------------------------------------
answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful ML tutor. Answer ONLY using the provided context.\n"
            "If the context is empty or insufficient, say: 'I don't know.'",
        ),
        ("human", "Question: {question}\n\nContext:\n{context}"),
    ]
)


def generate(state: State) -> State:
    out = (answer_prompt | llm).invoke({"question": state["question"], "context": state["refined_context"]})
    return {"answer": out.content}


# -------------------------------------------------------------------
# Routing (exact from Notebook 4)
# -------------------------------------------------------------------
def route_after_eval(state: State) -> str:
    if state["verdict"] == "CORRECT":
        return "refine"
    else:
        return "rewrite_query"


# -------------------------------------------------------------------
# Build graph (exact from Notebook 4)
# -------------------------------------------------------------------
def build_crag_graph():
    """Build and compile the CRAG StateGraph."""
    g = StateGraph(State)

    g.add_node("retrieve", retrieve_node)
    g.add_node("eval_each_doc", eval_each_doc_node)

    g.add_node("rewrite_query", rewrite_query_node)
    g.add_node("web_search", web_search_node)

    g.add_node("refine", refine)
    g.add_node("generate", generate)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "eval_each_doc")

    g.add_conditional_edges(
        "eval_each_doc",
        route_after_eval,
        {
            "refine": "refine",
            "rewrite_query": "rewrite_query",
        },
    )

    # non-correct path
    g.add_edge("rewrite_query", "web_search")
    g.add_edge("web_search", "refine")

    # correct path already goes to refine
    g.add_edge("refine", "generate")
    g.add_edge("generate", END)

    app = g.compile()
    return app


# Singleton compiled graph
_compiled_graph = None


def get_crag_graph():
    """Return the singleton compiled CRAG graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_crag_graph()
    return _compiled_graph


# -------------------------------------------------------------------
# Run pipeline with state tracking
# -------------------------------------------------------------------
# Store the latest run's node states for the graph visualization API
_last_run_node_states: Dict[str, Dict[str, Any]] = {}


def run_crag_pipeline(question: str, user_id: int) -> dict:
    """
    Run the CRAG pipeline and return the final state.
    Tracks input/output states of each node.
    """
    global _last_run_node_states
    _last_run_node_states = {}

    graph = get_crag_graph()

    initial_state = {
        "question": question,
        "user_id": user_id,
        "docs": [],
        "good_docs": [],
        "verdict": "",
        "reason": "",
        "strips": [],
        "kept_strips": [],
        "refined_context": "",
        "web_query": "",
        "web_docs": [],
        "answer": "",
    }

    # Run with streaming to capture node states
    prev_state = copy.deepcopy(initial_state)

    for event in graph.stream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():
            _last_run_node_states[node_name] = {
                "input_state": _serialize_state(prev_state),
                "output_state": _serialize_state(node_output),
            }
            # Update prev_state with node output
            prev_state = {**prev_state, **node_output}

    return prev_state


def get_node_states() -> Dict[str, Dict[str, Any]]:
    """Return the node states from the last pipeline run."""
    return _last_run_node_states


def _serialize_state(state: dict) -> dict:
    """Serialize state for JSON response (convert Documents to dicts)."""
    serialized = {}
    for key, value in state.items():
        if isinstance(value, list):
            serialized[key] = [
                {"page_content": doc.page_content, "metadata": doc.metadata}
                if isinstance(doc, Document) else doc
                for doc in value
            ]
        elif isinstance(value, Document):
            serialized[key] = {"page_content": value.page_content, "metadata": value.metadata}
        else:
            serialized[key] = value
    return serialized


# -------------------------------------------------------------------
# Graph structure info for frontend visualization
# -------------------------------------------------------------------
GRAPH_NODES = [
    {"id": "__start__", "label": "START"},
    {"id": "retrieve", "label": "Retrieve Documents"},
    {"id": "eval_each_doc", "label": "Evaluate Documents"},
    {"id": "rewrite_query", "label": "Rewrite Query"},
    {"id": "web_search", "label": "Web Search"},
    {"id": "refine", "label": "Refine Context"},
    {"id": "generate", "label": "Generate Answer"},
    {"id": "__end__", "label": "END"},
]

GRAPH_EDGES = [
    {"source": "__start__", "target": "retrieve", "label": None, "is_conditional": False},
    {"source": "retrieve", "target": "eval_each_doc", "label": None, "is_conditional": False},
    {"source": "eval_each_doc", "target": "refine", "label": "CORRECT", "is_conditional": True},
    {"source": "eval_each_doc", "target": "rewrite_query", "label": "INCORRECT / AMBIGUOUS", "is_conditional": True},
    {"source": "rewrite_query", "target": "web_search", "label": None, "is_conditional": False},
    {"source": "web_search", "target": "refine", "label": None, "is_conditional": False},
    {"source": "refine", "target": "generate", "label": None, "is_conditional": False},
    {"source": "generate", "target": "__end__", "label": None, "is_conditional": False},
]
