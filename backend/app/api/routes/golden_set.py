"""Golden Set API endpoints.

CRUD operations for golden test sets and test cases,
plus import from holdout and batch evaluation runner.
"""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.database import get_db
from app.db.models import GoldenTestSet, GoldenTestCase, EvaluationRun
from app.api.schemas.golden_set import (
    GoldenSetCreate,
    GoldenSetResponse,
    GoldenSetDetail,
    GoldenSetUpdate,
    GoldenSetListResponse,
    TestCaseCreate,
    TestCaseResponse,
    TestCaseUpdate,
    BulkImportRequest,
    BulkImportResponse,
    RunTestSetRequest,
    RunTestSetResponse,
    EvaluationRunResponse,
    EvaluationRunListResponse
)
from app.core.ingestion.loader import BitetDatasetLoader
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ============== Golden Set CRUD ==============

@router.post("/", response_model=GoldenSetResponse)
async def create_golden_set(
    request: GoldenSetCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new golden test set."""
    # Check if name already exists
    existing = await db.execute(
        select(GoldenTestSet).where(GoldenTestSet.name == request.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Golden set '{request.name}' already exists")

    golden_set = GoldenTestSet(
        id=uuid4(),
        name=request.name,
        description=request.description,
        version=1,
        created_at=datetime.utcnow()
    )

    db.add(golden_set)
    await db.commit()
    await db.refresh(golden_set)

    return GoldenSetResponse(
        id=golden_set.id,
        name=golden_set.name,
        description=golden_set.description,
        version=golden_set.version,
        created_at=golden_set.created_at,
        updated_at=golden_set.updated_at,
        test_case_count=0
    )


@router.get("/", response_model=GoldenSetListResponse)
async def list_golden_sets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all golden test sets with pagination."""
    # Get total count
    total = await db.scalar(select(func.count(GoldenTestSet.id)))

    # Get paginated results with test case counts
    stmt = (
        select(GoldenTestSet)
        .order_by(desc(GoldenTestSet.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    golden_sets = result.scalars().all()

    # Get test case counts for each set
    responses = []
    for gs in golden_sets:
        count = await db.scalar(
            select(func.count(GoldenTestCase.id))
            .where(GoldenTestCase.test_set_id == gs.id)
        )
        responses.append(GoldenSetResponse(
            id=gs.id,
            name=gs.name,
            description=gs.description,
            version=gs.version,
            created_at=gs.created_at,
            updated_at=gs.updated_at,
            test_case_count=count or 0
        ))

    return GoldenSetListResponse(
        golden_sets=responses,
        total=total or 0,
        skip=skip,
        limit=limit
    )


@router.get("/{golden_set_id}", response_model=GoldenSetDetail)
async def get_golden_set(
    golden_set_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a golden set with all its test cases."""
    # Get golden set
    gs = await db.get(GoldenTestSet, golden_set_id)
    if not gs:
        raise HTTPException(status_code=404, detail="Golden set not found")

    # Get test cases
    stmt = (
        select(GoldenTestCase)
        .where(GoldenTestCase.test_set_id == golden_set_id)
        .order_by(GoldenTestCase.created_at)
    )
    result = await db.execute(stmt)
    test_cases = result.scalars().all()

    return GoldenSetDetail(
        id=gs.id,
        name=gs.name,
        description=gs.description,
        version=gs.version,
        created_at=gs.created_at,
        updated_at=gs.updated_at,
        test_cases=[
            TestCaseResponse(
                id=tc.id,
                test_set_id=tc.test_set_id,
                query=tc.query,
                expected_answer=tc.expected_answer,
                category=tc.category,
                intent=tc.intent,
                metadata=tc.case_metadata,
                created_at=tc.created_at
            )
            for tc in test_cases
        ]
    )


@router.patch("/{golden_set_id}", response_model=GoldenSetResponse)
async def update_golden_set(
    golden_set_id: UUID,
    request: GoldenSetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a golden set's name or description."""
    gs = await db.get(GoldenTestSet, golden_set_id)
    if not gs:
        raise HTTPException(status_code=404, detail="Golden set not found")

    if request.name is not None:
        gs.name = request.name
    if request.description is not None:
        gs.description = request.description

    gs.updated_at = datetime.utcnow()
    gs.version += 1

    await db.commit()
    await db.refresh(gs)

    # Get test case count
    count = await db.scalar(
        select(func.count(GoldenTestCase.id))
        .where(GoldenTestCase.test_set_id == gs.id)
    )

    return GoldenSetResponse(
        id=gs.id,
        name=gs.name,
        description=gs.description,
        version=gs.version,
        created_at=gs.created_at,
        updated_at=gs.updated_at,
        test_case_count=count or 0
    )


@router.delete("/{golden_set_id}")
async def delete_golden_set(
    golden_set_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a golden set and all its test cases."""
    gs = await db.get(GoldenTestSet, golden_set_id)
    if not gs:
        raise HTTPException(status_code=404, detail="Golden set not found")

    await db.delete(gs)
    await db.commit()

    return {"message": f"Golden set '{gs.name}' deleted"}


# ============== Test Case CRUD ==============

@router.post("/{golden_set_id}/cases", response_model=TestCaseResponse)
async def add_test_case(
    golden_set_id: UUID,
    request: TestCaseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a test case to a golden set."""
    # Verify golden set exists
    gs = await db.get(GoldenTestSet, golden_set_id)
    if not gs:
        raise HTTPException(status_code=404, detail="Golden set not found")

    test_case = GoldenTestCase(
        id=uuid4(),
        test_set_id=golden_set_id,
        query=request.query,
        expected_answer=request.expected_answer,
        category=request.category,
        intent=request.intent,
        case_metadata=request.metadata,
        created_at=datetime.utcnow()
    )

    db.add(test_case)

    # Update golden set version
    gs.updated_at = datetime.utcnow()
    gs.version += 1

    await db.commit()
    await db.refresh(test_case)

    return TestCaseResponse(
        id=test_case.id,
        test_set_id=test_case.test_set_id,
        query=test_case.query,
        expected_answer=test_case.expected_answer,
        category=test_case.category,
        intent=test_case.intent,
        metadata=test_case.case_metadata,
        created_at=test_case.created_at
    )


@router.post("/{golden_set_id}/cases/bulk", response_model=dict)
async def add_test_cases_bulk(
    golden_set_id: UUID,
    cases: List[TestCaseCreate],
    db: AsyncSession = Depends(get_db)
):
    """Add multiple test cases to a golden set."""
    gs = await db.get(GoldenTestSet, golden_set_id)
    if not gs:
        raise HTTPException(status_code=404, detail="Golden set not found")

    added = 0
    for case in cases:
        test_case = GoldenTestCase(
            id=uuid4(),
            test_set_id=golden_set_id,
            query=case.query,
            expected_answer=case.expected_answer,
            category=case.category,
            intent=case.intent,
            metadata=case.case_metadata,
            created_at=datetime.utcnow()
        )
        db.add(test_case)
        added += 1

    gs.updated_at = datetime.utcnow()
    gs.version += 1

    await db.commit()

    return {"added": added, "golden_set_id": str(golden_set_id)}


@router.get("/{golden_set_id}/cases/{case_id}", response_model=TestCaseResponse)
async def get_test_case(
    golden_set_id: UUID,
    case_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific test case."""
    tc = await db.get(GoldenTestCase, case_id)
    if not tc or tc.test_set_id != golden_set_id:
        raise HTTPException(status_code=404, detail="Test case not found")

    return TestCaseResponse(
        id=tc.id,
        test_set_id=tc.test_set_id,
        query=tc.query,
        expected_answer=tc.expected_answer,
        category=tc.category,
        intent=tc.intent,
        metadata=tc.case_metadata,
        created_at=tc.created_at
    )


@router.patch("/{golden_set_id}/cases/{case_id}", response_model=TestCaseResponse)
async def update_test_case(
    golden_set_id: UUID,
    case_id: UUID,
    request: TestCaseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a test case."""
    tc = await db.get(GoldenTestCase, case_id)
    if not tc or tc.test_set_id != golden_set_id:
        raise HTTPException(status_code=404, detail="Test case not found")

    if request.query is not None:
        tc.query = request.query
    if request.expected_answer is not None:
        tc.expected_answer = request.expected_answer
    if request.category is not None:
        tc.category = request.category
    if request.intent is not None:
        tc.intent = request.intent
    if request.metadata is not None:
        tc.case_metadata = request.metadata

    # Update golden set version
    gs = await db.get(GoldenTestSet, golden_set_id)
    if gs:
        gs.updated_at = datetime.utcnow()
        gs.version += 1

    await db.commit()
    await db.refresh(tc)

    return TestCaseResponse(
        id=tc.id,
        test_set_id=tc.test_set_id,
        query=tc.query,
        expected_answer=tc.expected_answer,
        category=tc.category,
        intent=tc.intent,
        metadata=tc.case_metadata,
        created_at=tc.created_at
    )


@router.delete("/{golden_set_id}/cases/{case_id}")
async def delete_test_case(
    golden_set_id: UUID,
    case_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a test case."""
    tc = await db.get(GoldenTestCase, case_id)
    if not tc or tc.test_set_id != golden_set_id:
        raise HTTPException(status_code=404, detail="Test case not found")

    await db.delete(tc)

    # Update golden set version
    gs = await db.get(GoldenTestSet, golden_set_id)
    if gs:
        gs.updated_at = datetime.utcnow()
        gs.version += 1

    await db.commit()

    return {"message": "Test case deleted"}


# ============== Import from Holdout ==============

@router.post("/import-holdout", response_model=BulkImportResponse)
async def import_from_holdout(
    golden_set_id: UUID,
    max_cases: Optional[int] = Query(None, description="Max cases to import"),
    categories: Optional[List[str]] = Query(None, description="Filter by categories"),
    intents: Optional[List[str]] = Query(None, description="Filter by intents"),
    db: AsyncSession = Depends(get_db)
):
    """Import test cases from the stratified holdout set.

    This imports from the 20% test split created during data ingestion.
    """
    # Verify golden set exists
    gs = await db.get(GoldenTestSet, golden_set_id)
    if not gs:
        raise HTTPException(status_code=404, detail="Golden set not found")

    try:
        # Load holdout data
        loader = BitetDatasetLoader(raw_data_path=settings.raw_data_path)
        holdout_items = loader.load_split("test")
    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Holdout set not found. Run data ingestion with stratified split first."
        )

    imported = 0
    skipped = 0
    errors = []

    for item in holdout_items:
        # Apply filters
        if categories and item.get("category", "").upper() not in [c.upper() for c in categories]:
            skipped += 1
            continue

        if intents and item.get("intent", "").lower() not in [i.lower() for i in intents]:
            skipped += 1
            continue

        # Check max_cases limit
        if max_cases and imported >= max_cases:
            break

        try:
            test_case = GoldenTestCase(
                id=uuid4(),
                test_set_id=golden_set_id,
                query=item["instruction"],
                expected_answer=item["response"],
                category=item.get("category"),
                intent=item.get("intent"),
                case_metadata={
                    "flags": item.get("flags"),
                    "original_index": item.get("original_index"),
                    "source_id": item.get("source_id")
                },
                created_at=datetime.utcnow()
            )
            db.add(test_case)
            imported += 1

        except Exception as e:
            errors.append(str(e))

    # Update golden set
    gs.updated_at = datetime.utcnow()
    gs.version += 1

    await db.commit()

    return BulkImportResponse(
        test_set_id=golden_set_id,
        imported_count=imported,
        skipped_count=skipped,
        errors=errors[:10]  # Limit error messages
    )


# ============== Run Evaluation ==============

@router.post("/{golden_set_id}/run", response_model=RunTestSetResponse)
async def run_golden_set_evaluation(
    golden_set_id: UUID,
    request: RunTestSetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Run evaluation on all test cases in a golden set.

    This triggers the RAG pipeline for each test case and evaluates results.
    Runs in background for large sets.
    """
    # Verify golden set exists and get test cases
    gs = await db.get(GoldenTestSet, golden_set_id)
    if not gs:
        raise HTTPException(status_code=404, detail="Golden set not found")

    # Count test cases
    case_count = await db.scalar(
        select(func.count(GoldenTestCase.id))
        .where(GoldenTestCase.test_set_id == golden_set_id)
    )

    if not case_count:
        raise HTTPException(status_code=400, detail="Golden set has no test cases")

    # Create evaluation run record
    run = EvaluationRun(
        id=uuid4(),
        test_set_id=golden_set_id,
        config_snapshot={
            "llm_provider": request.llm_provider,
            "evaluator_provider": request.evaluator_provider,
            "top_k": request.top_k,
            "run_name": request.run_name
        },
        status="pending",
        started_at=datetime.utcnow()
    )

    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Queue background task for actual evaluation
    background_tasks.add_task(
        _run_evaluation_task,
        run_id=run.id,
        golden_set_id=golden_set_id,
        config=request
    )

    return RunTestSetResponse(
        run_id=run.id,
        test_set_id=golden_set_id,
        test_set_name=gs.name,
        status="pending",
        total_cases=case_count,
        completed_cases=0,
        failed_cases=0,
        results=None,
        summary=None,
        started_at=run.started_at,
        completed_at=None
    )


async def _run_evaluation_task(
    run_id: UUID,
    golden_set_id: UUID,
    config: RunTestSetRequest
):
    """Background task to run golden set evaluation with RAGAS.

    This is called asynchronously after the API returns.
    """
    # Import here to avoid circular imports
    from app.db.database import async_session_maker
    from app.core.retrieval.retriever import RAGRetriever
    from app.evaluation.ragas import RAGASEvaluator

    async with async_session_maker() as db:
        try:
            # Update status to running
            run = await db.get(EvaluationRun, run_id)
            if not run:
                return

            run.status = "running"
            await db.commit()

            # Get all test cases
            stmt = select(GoldenTestCase).where(GoldenTestCase.test_set_id == golden_set_id)
            result = await db.execute(stmt)
            test_cases = result.scalars().all()

            # Initialize RAG and RAGAS evaluator
            retriever = RAGRetriever(llm_provider=config.llm_provider)
            evaluator = RAGASEvaluator(provider=config.evaluator_provider)

            results = []
            completed = 0
            failed = 0
            total_score = 0

            for tc in test_cases:
                try:
                    # Run RAG pipeline
                    rag_result = await retriever.query(
                        query=tc.query,
                        top_k=config.top_k
                    )

                    # Evaluate response with RAGAS (with ground truth)
                    evaluation = await evaluator.evaluate_response(
                        query=tc.query,
                        response=rag_result["response"],
                        contexts=rag_result["sources"],
                        expected_answer=tc.expected_answer
                    )

                    score = evaluation.get("overall_score", 0)
                    total_score += score if score else 0
                    completed += 1

                    results.append({
                        "test_case_id": str(tc.id),
                        "query": tc.query,
                        "expected_answer": tc.expected_answer,
                        "generated_answer": rag_result["response"],
                        "overall_score": score,
                        "scores": evaluation.get("scores", {}),
                        "status": "success",
                        "has_ground_truth": evaluation.get("has_ground_truth", True)
                    })

                except Exception as e:
                    logger.error(f"Failed to evaluate test case {tc.id}: {e}")
                    failed += 1
                    results.append({
                        "test_case_id": str(tc.id),
                        "query": tc.query,
                        "status": "error",
                        "error": str(e)
                    })

            # Calculate summary
            avg_score = total_score / completed if completed > 0 else None
            summary = {
                "total_cases": len(test_cases),
                "completed": completed,
                "failed": failed,
                "avg_score": round(avg_score, 2) if avg_score else None,
                "pass_rate": round(completed / len(test_cases) * 100, 1) if test_cases else 0,
                "evaluation_type": "ragas"
            }

            # Update run record
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            run.results_json = {
                "results": results,
                "summary": summary
            }

            await db.commit()

        except Exception as e:
            logger.error(f"Evaluation run {run_id} failed: {e}")
            run = await db.get(EvaluationRun, run_id)
            if run:
                run.status = "failed"
                run.results_json = {"error": str(e)}
                await db.commit()


@router.get("/{golden_set_id}/runs", response_model=EvaluationRunListResponse)
async def list_evaluation_runs(
    golden_set_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all evaluation runs for a golden set."""
    stmt = (
        select(EvaluationRun)
        .where(EvaluationRun.test_set_id == golden_set_id)
        .order_by(desc(EvaluationRun.started_at))
    )
    result = await db.execute(stmt)
    runs = result.scalars().all()

    return EvaluationRunListResponse(
        runs=[
            EvaluationRunResponse(
                id=r.id,
                test_set_id=r.test_set_id,
                status=r.status,
                config_snapshot=r.config_snapshot,
                results_json=r.results_json,
                started_at=r.started_at,
                completed_at=r.completed_at
            )
            for r in runs
        ],
        total=len(runs)
    )


@router.get("/{golden_set_id}/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation_run(
    golden_set_id: UUID,
    run_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific evaluation run."""
    run = await db.get(EvaluationRun, run_id)
    if not run or run.test_set_id != golden_set_id:
        raise HTTPException(status_code=404, detail="Evaluation run not found")

    return EvaluationRunResponse(
        id=run.id,
        test_set_id=run.test_set_id,
        status=run.status,
        config_snapshot=run.config_snapshot,
        results_json=run.results_json,
        started_at=run.started_at,
        completed_at=run.completed_at
    )
