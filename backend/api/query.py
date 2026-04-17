from fastapi import APIRouter, HTTPException
from typing import List

from schemas.request_models import QueryRequest
from schemas.response_models import QueryResponse
from graph.crag_graph import run_crag_pipeline
from services.history import save_query, get_history

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Run the CRAG graph pipeline for a user question.
    Returns the final answer along with pipeline metadata.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = run_crag_pipeline(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    # Count good_docs
    good_docs = result.get("good_docs", [])
    num_good = len(good_docs) if good_docs else 0

    kept_strips = result.get("kept_strips", [])
    num_kept = len(kept_strips) if kept_strips else 0

    answer = result.get("answer", "")
    verdict = result.get("verdict", "")
    reason = result.get("reason", "")

    # Save to history
    save_query(request.question, answer, verdict, reason)

    return QueryResponse(
        answer=answer,
        verdict=verdict,
        reason=reason,
        web_query=result.get("web_query", ""),
        num_good_docs=num_good,
        num_kept_strips=num_kept,
    )


@router.get("/history")
async def fetch_history():
    """Returns the last 20 questions and answers."""
    return get_history()
