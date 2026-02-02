"""Diagnosis API endpoints.

Endpoints for analyzing evaluations and getting improvement suggestions.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.evaluation.diagnosis.agent import DiagnosisAgent, report_to_dict

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/report")
async def get_diagnosis_report(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Generate a full diagnosis report.

    Analyzes evaluations from the specified period and identifies:
    - Performance issues
    - Categories/intents that need attention
    - Suggested actions for improvement

    This may take a few seconds as it uses LLM analysis.
    """
    agent = DiagnosisAgent(db)
    report = await agent.generate_report(days=days)
    return report_to_dict(report)


@router.get("/summary")
async def get_quick_summary(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Get a quick summary of evaluation health.

    Faster than full report - useful for dashboards.
    Returns key metrics and alerts without full LLM analysis.
    """
    agent = DiagnosisAgent(db)
    return await agent.get_quick_summary(days=days)


@router.get("/alerts")
async def get_alerts(
    days: int = Query(7, ge=1, le=90),
    severity: Optional[str] = Query(None, description="Filter by severity: high, medium, low"),
    db: AsyncSession = Depends(get_db)
):
    """Get active alerts based on recent evaluations.

    Returns alerts for issues that need attention.
    """
    agent = DiagnosisAgent(db)
    summary = await agent.get_quick_summary(days=days)

    alerts = summary.get("alerts", [])

    # Filter by severity if specified
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]

    return {
        "alerts": alerts,
        "total_alerts": len(alerts),
        "period_days": days
    }
