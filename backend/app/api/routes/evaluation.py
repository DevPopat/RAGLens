"""Evaluation API endpoints.

Endpoints for running evaluations and viewing results.
"""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.db.database import get_db
from app.db.models import Evaluation, Query as QueryModel, Response as ResponseModel
from app.api.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationListResponse,
    BatchEvaluationRequest,
    BatchEvaluationResponse
)
from app.evaluation.generation.llm_judge import LLMJudge, evaluate_with_llm
from app.evaluation.retrieval.relevance import RetrievalEvaluator
from app.core.retrieval.retriever import RAGRetriever
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run", response_model=EvaluationResponse)
async def run_evaluation(
    request: EvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Run evaluation on a specific query response.

    This evaluates an existing query/response pair using:
    - LLM-as-judge for generation quality
    - Retrieval metrics if relevant_doc_ids provided
    """
    try:
        # Fetch the query and response
        stmt = (
            select(QueryModel, ResponseModel)
            .join(ResponseModel, QueryModel.id == ResponseModel.query_id)
            .where(QueryModel.id == request.query_id)
        )
        result = await db.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Query not found")

        query_obj, response_obj = row

        # Parse contexts from response
        contexts = response_obj.sources_json or []

        # Run LLM-as-judge evaluation
        llm_judge = LLMJudge(
            provider=request.evaluator_provider or "anthropic"
        )

        evaluation_result = await llm_judge.evaluate_response(
            query=query_obj.query_text,
            response=response_obj.response_text,
            contexts=contexts,
            expected_category=request.expected_category,
            expected_intent=request.expected_intent
        )

        # Run retrieval evaluation if relevant docs provided
        retrieval_metrics = None
        if request.relevant_doc_ids:
            retrieval_evaluator = RetrievalEvaluator()
            retrieval_metrics = retrieval_evaluator.evaluate_retrieval(
                retrieved_docs=contexts,
                relevant_doc_ids=set(request.relevant_doc_ids),
                k_values=[1, 3, 5]
            )

        # Combine evaluations
        combined_scores = {
            "generation": evaluation_result.get("scores", {}),
            "overall_score": evaluation_result.get("overall_score"),
            "retrieval": retrieval_metrics
        }

        # Store evaluation in database
        evaluation = Evaluation(
            id=uuid4(),
            query_id=request.query_id,
            evaluation_type="llm_judge",
            scores_json=combined_scores,
            evaluator=evaluation_result.get("evaluator", "unknown"),
            metadata_json={
                "expected_category": request.expected_category,
                "expected_intent": request.expected_intent,
                "evaluation_detail": {
                    "explanation": evaluation_result.get("explanation"),
                    "strengths": evaluation_result.get("strengths", []),
                    "weaknesses": evaluation_result.get("weaknesses", []),
                    "suggested_improvement": evaluation_result.get("suggested_improvement")
                }
            },
            timestamp=datetime.utcnow()
        )

        db.add(evaluation)
        await db.commit()
        await db.refresh(evaluation)

        return EvaluationResponse(
            id=evaluation.id,
            query_id=evaluation.query_id,
            evaluation_type=evaluation.evaluation_type,
            scores=combined_scores,
            evaluator=evaluation.evaluator,
            metadata=evaluation.metadata_json,
            timestamp=evaluation.timestamp
        )

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchEvaluationResponse)
async def run_batch_evaluation(
    request: BatchEvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Run evaluation on multiple queries in batch.

    Useful for evaluating golden sets or regression testing.
    """
    try:
        results = []
        errors = []

        llm_judge = LLMJudge(provider=request.evaluator_provider or "anthropic")

        for query_id in request.query_ids:
            try:
                # Fetch query and response
                stmt = (
                    select(QueryModel, ResponseModel)
                    .join(ResponseModel, QueryModel.id == ResponseModel.query_id)
                    .where(QueryModel.id == query_id)
                )
                result = await db.execute(stmt)
                row = result.first()

                if not row:
                    errors.append({
                        "query_id": str(query_id),
                        "error": "Query not found"
                    })
                    continue

                query_obj, response_obj = row
                contexts = response_obj.sources_json or []

                # Evaluate
                evaluation_result = await llm_judge.evaluate_response(
                    query=query_obj.query_text,
                    response=response_obj.response_text,
                    contexts=contexts
                )

                # Store evaluation
                evaluation = Evaluation(
                    id=uuid4(),
                    query_id=query_id,
                    evaluation_type="llm_judge_batch",
                    scores_json={
                        "generation": evaluation_result.get("scores", {}),
                        "overall_score": evaluation_result.get("overall_score")
                    },
                    evaluator=evaluation_result.get("evaluator"),
                    metadata_json={
                        "batch_id": request.batch_name,
                        "explanation": evaluation_result.get("explanation")
                    },
                    timestamp=datetime.utcnow()
                )

                db.add(evaluation)
                results.append({
                    "query_id": str(query_id),
                    "overall_score": evaluation_result.get("overall_score"),
                    "status": "success"
                })

            except Exception as e:
                logger.error(f"Failed to evaluate query {query_id}: {e}")
                errors.append({
                    "query_id": str(query_id),
                    "error": str(e)
                })

        await db.commit()

        # Calculate summary statistics
        scores = [r["overall_score"] for r in results if r.get("overall_score") is not None]
        summary = {
            "total_evaluated": len(results),
            "total_errors": len(errors),
            "avg_score": sum(scores) / len(scores) if scores else None,
            "min_score": min(scores) if scores else None,
            "max_score": max(scores) if scores else None
        }

        return BatchEvaluationResponse(
            batch_name=request.batch_name,
            total_queries=len(request.query_ids),
            successful=len(results),
            failed=len(errors),
            results=results,
            errors=errors,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Batch evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get evaluation details by ID."""
    stmt = select(Evaluation).where(Evaluation.id == evaluation_id)
    result = await db.execute(stmt)
    evaluation = result.scalar_one_or_none()

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return EvaluationResponse(
        id=evaluation.id,
        query_id=evaluation.query_id,
        evaluation_type=evaluation.evaluation_type,
        scores=evaluation.scores_json,
        evaluator=evaluation.evaluator,
        metadata=evaluation.metadata_json,
        timestamp=evaluation.timestamp
    )


@router.get("/", response_model=EvaluationListResponse)
async def list_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    evaluation_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all evaluations with pagination."""
    # Build query
    stmt = select(Evaluation).order_by(desc(Evaluation.timestamp))

    if evaluation_type:
        stmt = stmt.where(Evaluation.evaluation_type == evaluation_type)

    # Get total count efficiently using SQL COUNT
    count_stmt = select(func.count(Evaluation.id))
    if evaluation_type:
        count_stmt = count_stmt.where(Evaluation.evaluation_type == evaluation_type)

    total = await db.scalar(count_stmt) or 0

    # Get paginated results
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    evaluations = result.scalars().all()

    return EvaluationListResponse(
        evaluations=[
            EvaluationResponse(
                id=e.id,
                query_id=e.query_id,
                evaluation_type=e.evaluation_type,
                scores=e.scores_json,
                evaluator=e.evaluator,
                metadata=e.metadata_json,
                timestamp=e.timestamp
            )
            for e in evaluations
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/query/{query_id}", response_model=EvaluationListResponse)
async def get_evaluations_for_query(
    query_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all evaluations for a specific query."""
    stmt = (
        select(Evaluation)
        .where(Evaluation.query_id == query_id)
        .order_by(desc(Evaluation.timestamp))
    )

    result = await db.execute(stmt)
    evaluations = result.scalars().all()

    return EvaluationListResponse(
        evaluations=[
            EvaluationResponse(
                id=e.id,
                query_id=e.query_id,
                evaluation_type=e.evaluation_type,
                scores=e.scores_json,
                evaluator=e.evaluator,
                metadata=e.metadata_json,
                timestamp=e.timestamp
            )
            for e in evaluations
        ],
        total=len(evaluations),
        skip=0,
        limit=len(evaluations)
    )
