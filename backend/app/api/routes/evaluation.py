"""Evaluation API endpoints.

Endpoints for running evaluations and viewing results.
"""
import logging
import time
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
    BatchEvaluationResponse,
    ClaimCompareRequest,
    ClaimCompareResponse,
    Claim,
    DetailedAnalysisRequest,
    DetailedAnalysisResponse,
    FaithfulnessDetail,
    QuestionCoverageDetail,
    ContextUtilizationDetail,
)
import json
from app.evaluation.ragas import RAGASEvaluator
from app.core.generation.claude import ClaudeGenerator
from app.core.generation.openai_gen import OpenAIGenerator
from app.core.generation.prompt_templates import (
    CLAIM_COMPARE_PROMPT,
    CLAIM_COMPARE_SYSTEM_PROMPT,
    DETAILED_ANALYSIS_SYSTEM_PROMPT,
    DETAILED_ANALYSIS_PROMPT_HEADER,
    DETAILED_ANALYSIS_PROMPT_COVERAGE,
    DETAILED_ANALYSIS_PROMPT_CONTEXT,
    DETAILED_ANALYSIS_FORMAT_WITH_COVERAGE,
    DETAILED_ANALYSIS_FORMAT_WITHOUT_COVERAGE,
)
from app.api.routes.chat import _format_history_for_evaluation
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run", response_model=EvaluationResponse)
async def run_evaluation(
    request: EvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Run RAGAS evaluation on a specific query response.

    This evaluates an existing query/response pair using RAGAS metrics:
    - Context Precision: Are retrieved docs relevant?
    - Faithfulness: Is response grounded in context?
    - Answer Relevancy: Is answer relevant to question?
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

        # Enrich query with conversation history if provided
        eval_query = query_obj.query_text
        has_context = False
        if request.conversation_history:
            history_context = _format_history_for_evaluation(request.conversation_history)
            if history_context:
                eval_query = f"Conversation context:\n{history_context}\n\nCurrent question: {query_obj.query_text}"
                has_context = True

        # Run RAGAS evaluation
        evaluator = RAGASEvaluator(
            provider=request.evaluator_provider or "anthropic"
        )

        eval_start = time.perf_counter()
        evaluation_result = await evaluator.evaluate_response(
            query=eval_query,
            response=response_obj.response_text,
            contexts=contexts,
            expected_answer=None  # No ground truth for single query evaluation
        )
        eval_latency_ms = round((time.perf_counter() - eval_start) * 1000)

        # Store evaluation in database
        evaluation = Evaluation(
            id=uuid4(),
            query_id=request.query_id,
            evaluation_type="ragas",
            scores_json=evaluation_result.get("scores", {}),
            evaluator=evaluation_result.get("evaluator", "ragas/unknown"),
            metadata={
                "expected_category": request.expected_category,
                "expected_intent": request.expected_intent,
                "has_ground_truth": evaluation_result.get("has_ground_truth", False),
                "has_conversation_context": has_context,
                "metrics_used": evaluation_result.get("metrics_used", [])
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
            scores=evaluation.scores_json,
            evaluator=evaluation.evaluator,
            metadata=evaluation.eval_metadata,
            timestamp=evaluation.timestamp,
            latency_ms=eval_latency_ms,
        )

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchEvaluationResponse)
async def run_batch_evaluation(
    request: BatchEvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Run RAGAS evaluation on multiple queries in batch.

    Useful for evaluating golden sets or regression testing.
    """
    try:
        results = []
        errors = []

        evaluator = RAGASEvaluator(provider=request.evaluator_provider or "anthropic")

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

                # Evaluate with RAGAS
                evaluation_result = await evaluator.evaluate_response(
                    query=query_obj.query_text,
                    response=response_obj.response_text,
                    contexts=contexts,
                    expected_answer=None
                )

                # Store evaluation
                evaluation = Evaluation(
                    id=uuid4(),
                    query_id=query_id,
                    evaluation_type="ragas_batch",
                    scores_json=evaluation_result.get("scores", {}),
                    evaluator=evaluation_result.get("evaluator", "ragas/unknown"),
                    metadata={
                        "batch_id": request.batch_name,
                        "has_ground_truth": evaluation_result.get("has_ground_truth", False)
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
        metadata=evaluation.eval_metadata,
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
                metadata=e.eval_metadata,
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
                metadata=e.eval_metadata,
                timestamp=e.timestamp
            )
            for e in evaluations
        ],
        total=len(evaluations),
        skip=0,
        limit=len(evaluations)
    )


@router.post("/compare-claims", response_model=ClaimCompareResponse)
async def compare_claims(request: ClaimCompareRequest):
    """Compare expected vs generated answers at the claim level.

    Decomposes the expected answer into factual claims and checks each
    against the generated answer, returning status and relevant quotes.
    """
    try:
        prompt = CLAIM_COMPARE_PROMPT.format(
            expected_answer=request.expected_answer,
            generated_answer=request.generated_answer,
        )

        if settings.default_llm_provider == "openai":
            generator = OpenAIGenerator()
        else:
            generator = ClaudeGenerator()

        result = await generator.generate(
            prompt=prompt,
            system_prompt=CLAIM_COMPARE_SYSTEM_PROMPT,
            temperature=0.0,
        )

        parsed = json.loads(result["text"])
        claims = [
            Claim(
                claim=c["claim"],
                status=c["status"],
                detail=c["detail"],
                generated_quote=c.get("generated_quote"),
            )
            for c in parsed["claims"]
        ]

        return ClaimCompareResponse(claims=claims)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse claim comparison response: {e}")
        raise HTTPException(status_code=500, detail="LLM returned invalid JSON")
    except Exception as e:
        logger.error(f"Claim comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Message types that skip question coverage analysis
_SKIP_COVERAGE_TYPES = {"acknowledgment", "greeting", "closure"}


@router.post("/detailed-analysis", response_model=DetailedAnalysisResponse)
async def get_detailed_analysis(request: DetailedAnalysisRequest):
    """Get detailed, actionable analysis of a RAG evaluation.

    Lazy-loaded on-demand when the user wants to understand WHY a
    particular evaluation scored the way it did. Makes a single LLM call
    to analyze faithfulness (claim-level), question coverage, and context
    utilization.
    """
    try:
        # Format scores for the prompt
        scores_summary = ", ".join(
            f"{k}: {v:.0%}" for k, v in request.scores.items()
            if v is not None and k != "overall_score"
        )

        # Format contexts with indices
        contexts_formatted = "\n".join(
            f"[Context {i}]: {ctx}" for i, ctx in enumerate(request.contexts)
        )

        # Determine whether to include question coverage
        skip_coverage = (
            request.message_type in _SKIP_COVERAGE_TYPES
            if request.message_type
            else False
        )

        # Build prompt dynamically
        prompt_parts = [
            DETAILED_ANALYSIS_PROMPT_HEADER.format(
                query=request.query,
                response=request.response,
                contexts_formatted=contexts_formatted,
                scores_summary=scores_summary or "No scores available",
            )
        ]

        if not skip_coverage:
            prompt_parts.append(DETAILED_ANALYSIS_PROMPT_COVERAGE)
            section_num = 3
        else:
            section_num = 2

        prompt_parts.append(
            DETAILED_ANALYSIS_PROMPT_CONTEXT.format(section_num=section_num)
        )

        if skip_coverage:
            prompt_parts.append(DETAILED_ANALYSIS_FORMAT_WITHOUT_COVERAGE)
        else:
            prompt_parts.append(DETAILED_ANALYSIS_FORMAT_WITH_COVERAGE)

        prompt = "".join(prompt_parts)

        # Use the configured LLM provider
        if settings.default_llm_provider == "openai":
            generator = OpenAIGenerator()
        else:
            generator = ClaudeGenerator()

        result = await generator.generate(
            prompt=prompt,
            system_prompt=DETAILED_ANALYSIS_SYSTEM_PROMPT,
            temperature=0.0,
            max_tokens=4096,
        )

        parsed = json.loads(result["text"])

        # Build response, handling each section gracefully
        faithfulness = None
        if "faithfulness" in parsed:
            try:
                faithfulness = FaithfulnessDetail(**parsed["faithfulness"])
            except Exception as e:
                logger.warning(f"Failed to parse faithfulness detail: {e}")

        answer_relevancy = None
        if not skip_coverage and "answer_relevancy" in parsed:
            try:
                answer_relevancy = QuestionCoverageDetail(**parsed["answer_relevancy"])
            except Exception as e:
                logger.warning(f"Failed to parse answer_relevancy detail: {e}")

        context_precision = None
        if "context_precision" in parsed:
            try:
                context_precision = ContextUtilizationDetail(**parsed["context_precision"])
            except Exception as e:
                logger.warning(f"Failed to parse context_precision detail: {e}")

        return DetailedAnalysisResponse(
            faithfulness=faithfulness,
            answer_relevancy=answer_relevancy,
            context_precision=context_precision,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse detailed analysis response: {e}")
        raise HTTPException(
            status_code=500,
            detail="LLM returned invalid JSON for detailed analysis"
        )
    except Exception as e:
        logger.error(f"Detailed analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
