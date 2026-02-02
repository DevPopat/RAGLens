"""Diagnosis Agent for analyzing evaluations and suggesting improvements.

This agent:
1. Analyzes evaluation patterns to identify issues
2. Suggests actionable fixes (retrieval params, prompts, etc.)
3. Tracks which suggestions are safe to auto-apply vs need approval
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from anthropic import AsyncAnthropic

from app.db.models import Evaluation, Query
from app.config import settings

logger = logging.getLogger(__name__)


class IssueSeverity(str, Enum):
    """Severity levels for identified issues."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueCategory(str, Enum):
    """Categories of issues."""
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    KNOWLEDGE_GAP = "knowledge_gap"
    PROMPT = "prompt"
    LATENCY = "latency"


class ActionType(str, Enum):
    """Types of suggested actions."""
    AUTO_SAFE = "auto_safe"          # Can apply automatically
    NEEDS_APPROVAL = "needs_approval"  # Suggest but don't auto-apply
    MANUAL = "manual"                # Requires human intervention


@dataclass
class Issue:
    """An identified issue from evaluation analysis."""
    id: str
    category: IssueCategory
    severity: IssueSeverity
    description: str
    affected_count: int
    example_queries: List[str]
    metrics: Dict[str, Any]


@dataclass
class Action:
    """A suggested action to fix an issue."""
    id: str
    issue_id: str
    action_type: ActionType
    description: str
    parameter_changes: Optional[Dict[str, Any]] = None
    expected_improvement: Optional[str] = None


@dataclass
class DiagnosisReport:
    """Complete diagnosis report."""
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_evaluations: int
    avg_score: Optional[float]
    issues: List[Issue]
    actions: List[Action]
    summary: str


DIAGNOSIS_PROMPT = """You are a RAG system diagnostician. Analyze these evaluation metrics and identify issues.

EVALUATION SUMMARY:
- Total evaluations: {total_evaluations}
- Average score: {avg_score:.2f}/5
- Period: {period_start} to {period_end}

SCORE BREAKDOWN BY CATEGORY:
{category_breakdown}

SCORE BREAKDOWN BY INTENT:
{intent_breakdown}

LOW-SCORING QUERIES (score < 3.5):
{low_scoring_queries}

SCORE DISTRIBUTION:
{score_distribution}

Based on this data, identify:
1. Key issues affecting performance
2. Patterns in low-scoring queries
3. Categories/intents that need attention
4. Specific actionable recommendations

Respond in JSON format:
{{
    "issues": [
        {{
            "category": "retrieval|generation|knowledge_gap|prompt|latency",
            "severity": "high|medium|low",
            "description": "Description of the issue",
            "affected_queries_pattern": "Pattern description",
            "suggested_fix": "Specific recommendation"
        }}
    ],
    "summary": "Overall assessment in 2-3 sentences"
}}
"""


class DiagnosisAgent:
    """Agent that analyzes evaluations and suggests improvements."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_report(
        self,
        days: int = 7,
        min_evaluations: int = 10
    ) -> DiagnosisReport:
        """Generate a diagnosis report for recent evaluations.

        Args:
            days: Number of days to analyze
            min_evaluations: Minimum evaluations required for analysis

        Returns:
            DiagnosisReport with issues and suggested actions
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        # Gather metrics
        metrics = await self._gather_metrics(period_start, period_end)

        if metrics["total_evaluations"] < min_evaluations:
            return DiagnosisReport(
                generated_at=datetime.utcnow(),
                period_start=period_start,
                period_end=period_end,
                total_evaluations=metrics["total_evaluations"],
                avg_score=metrics.get("avg_score"),
                issues=[],
                actions=[],
                summary=f"Insufficient data: Only {metrics['total_evaluations']} evaluations found. Need at least {min_evaluations}."
            )

        # Analyze with LLM
        analysis = await self._analyze_with_llm(metrics, period_start, period_end)

        # Convert to issues and actions
        issues = self._create_issues(analysis, metrics)
        actions = self._create_actions(issues)

        return DiagnosisReport(
            generated_at=datetime.utcnow(),
            period_start=period_start,
            period_end=period_end,
            total_evaluations=metrics["total_evaluations"],
            avg_score=metrics.get("avg_score"),
            issues=issues,
            actions=actions,
            summary=analysis.get("summary", "Analysis complete.")
        )

    async def _gather_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Gather evaluation metrics for analysis."""
        # Base filter
        date_filter = and_(
            Evaluation.timestamp >= start_date,
            Evaluation.timestamp <= end_date
        )

        # Total count
        total = await self.db.scalar(
            select(func.count(Evaluation.id)).where(date_filter)
        )

        # Get all evaluations with their queries
        stmt = (
            select(Evaluation, Query)
            .join(Query, Evaluation.query_id == Query.id)
            .where(date_filter)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            return {"total_evaluations": 0}

        # Process evaluations
        scores = []
        category_scores = defaultdict(list)
        intent_scores = defaultdict(list)
        low_scoring = []
        score_buckets = {"1-2": 0, "2-3": 0, "3-4": 0, "4-5": 0}

        for eval_obj, query_obj in rows:
            score = None
            if eval_obj.scores_json:
                score = eval_obj.scores_json.get("overall_score")
                if score is None and "generation" in eval_obj.scores_json:
                    # Try to get from nested structure
                    gen_scores = eval_obj.scores_json.get("generation", {})
                    if gen_scores:
                        score = sum(gen_scores.values()) / len(gen_scores)

            if score is not None:
                scores.append(score)

                # Get category/intent from query config
                config = query_obj.retrieval_config or {}
                category = config.get("filter_category", "unknown")
                intent = config.get("filter_intent", "unknown")

                category_scores[category].append(score)
                intent_scores[intent].append(score)

                # Bucket distribution
                if score < 2:
                    score_buckets["1-2"] += 1
                elif score < 3:
                    score_buckets["2-3"] += 1
                elif score < 4:
                    score_buckets["3-4"] += 1
                else:
                    score_buckets["4-5"] += 1

                # Track low-scoring
                if score < 3.5:
                    low_scoring.append({
                        "query": query_obj.query_text[:100],
                        "score": score,
                        "category": category,
                        "intent": intent
                    })

        avg_score = sum(scores) / len(scores) if scores else None

        # Calculate category averages
        category_breakdown = {
            cat: {
                "avg": sum(s) / len(s),
                "count": len(s)
            }
            for cat, s in category_scores.items()
        }

        intent_breakdown = {
            intent: {
                "avg": sum(s) / len(s),
                "count": len(s)
            }
            for intent, s in intent_scores.items()
        }

        return {
            "total_evaluations": total,
            "avg_score": avg_score,
            "category_breakdown": category_breakdown,
            "intent_breakdown": intent_breakdown,
            "low_scoring_queries": low_scoring[:10],  # Top 10
            "score_distribution": score_buckets
        }

    async def _analyze_with_llm(
        self,
        metrics: Dict[str, Any],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Use LLM to analyze metrics and identify issues."""
        # Format metrics for prompt
        category_str = "\n".join([
            f"  {cat}: avg={data['avg']:.2f}, count={data['count']}"
            for cat, data in metrics.get("category_breakdown", {}).items()
        ])

        intent_str = "\n".join([
            f"  {intent}: avg={data['avg']:.2f}, count={data['count']}"
            for intent, data in list(metrics.get("intent_breakdown", {}).items())[:10]
        ])

        low_scoring_str = "\n".join([
            f"  - \"{q['query'][:50]}...\" (score: {q['score']:.1f}, {q['category']}/{q['intent']})"
            for q in metrics.get("low_scoring_queries", [])[:5]
        ])

        score_dist_str = "\n".join([
            f"  {bucket}: {count} evaluations"
            for bucket, count in metrics.get("score_distribution", {}).items()
        ])

        prompt = DIAGNOSIS_PROMPT.format(
            total_evaluations=metrics["total_evaluations"],
            avg_score=metrics.get("avg_score", 0),
            period_start=period_start.strftime("%Y-%m-%d"),
            period_end=period_end.strftime("%Y-%m-%d"),
            category_breakdown=category_str or "  No category data",
            intent_breakdown=intent_str or "  No intent data",
            low_scoring_queries=low_scoring_str or "  None",
            score_distribution=score_dist_str
        )

        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",  # Fast, cheap for analysis
                max_tokens=1000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text

            # Parse JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            return json.loads(result_text.strip())

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                "issues": [],
                "summary": f"Analysis failed: {str(e)}"
            }

    def _create_issues(
        self,
        analysis: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> List[Issue]:
        """Convert LLM analysis to Issue objects."""
        issues = []

        for i, issue_data in enumerate(analysis.get("issues", [])):
            try:
                issue = Issue(
                    id=f"issue_{i+1}",
                    category=IssueCategory(issue_data.get("category", "generation")),
                    severity=IssueSeverity(issue_data.get("severity", "medium")),
                    description=issue_data.get("description", "Unknown issue"),
                    affected_count=len(metrics.get("low_scoring_queries", [])),
                    example_queries=[
                        q["query"] for q in metrics.get("low_scoring_queries", [])[:3]
                    ],
                    metrics={
                        "suggested_fix": issue_data.get("suggested_fix"),
                        "pattern": issue_data.get("affected_queries_pattern")
                    }
                )
                issues.append(issue)
            except Exception as e:
                logger.error(f"Failed to create issue: {e}")

        return issues

    def _create_actions(self, issues: List[Issue]) -> List[Action]:
        """Generate actions for identified issues."""
        actions = []

        for issue in issues:
            # Generate action based on issue category
            if issue.category == IssueCategory.RETRIEVAL:
                actions.append(Action(
                    id=f"action_{issue.id}_1",
                    issue_id=issue.id,
                    action_type=ActionType.AUTO_SAFE,
                    description="Increase top_k retrieval parameter",
                    parameter_changes={"top_k": {"from": 5, "to": 7}},
                    expected_improvement="May improve recall by retrieving more relevant documents"
                ))

            elif issue.category == IssueCategory.GENERATION:
                actions.append(Action(
                    id=f"action_{issue.id}_1",
                    issue_id=issue.id,
                    action_type=ActionType.NEEDS_APPROVAL,
                    description="Update system prompt for better response quality",
                    parameter_changes=None,
                    expected_improvement="May improve response accuracy and tone"
                ))

            elif issue.category == IssueCategory.KNOWLEDGE_GAP:
                actions.append(Action(
                    id=f"action_{issue.id}_1",
                    issue_id=issue.id,
                    action_type=ActionType.MANUAL,
                    description=f"Add more training data for: {issue.metrics.get('pattern', 'identified gap')}",
                    parameter_changes=None,
                    expected_improvement="Will enable RAG to answer currently unsupported queries"
                ))

            elif issue.category == IssueCategory.LATENCY:
                actions.append(Action(
                    id=f"action_{issue.id}_1",
                    issue_id=issue.id,
                    action_type=ActionType.AUTO_SAFE,
                    description="Reduce top_k to improve latency",
                    parameter_changes={"top_k": {"from": 5, "to": 3}},
                    expected_improvement="May reduce response time by 20-30%"
                ))

            # Add the LLM's suggested fix as an action
            if issue.metrics.get("suggested_fix"):
                actions.append(Action(
                    id=f"action_{issue.id}_llm",
                    issue_id=issue.id,
                    action_type=ActionType.NEEDS_APPROVAL,
                    description=issue.metrics["suggested_fix"],
                    parameter_changes=None,
                    expected_improvement="LLM-suggested improvement"
                ))

        return actions

    async def get_quick_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get a quick summary without full LLM analysis.

        Useful for dashboards and monitoring.
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days)

        metrics = await self._gather_metrics(period_start, period_end)

        # Identify obvious issues without LLM
        alerts = []

        avg_score = metrics.get("avg_score")
        if avg_score and avg_score < 3.5:
            alerts.append({
                "type": "low_avg_score",
                "severity": "high" if avg_score < 3.0 else "medium",
                "message": f"Average score is {avg_score:.2f}/5"
            })

        # Check for categories with low scores
        for cat, data in metrics.get("category_breakdown", {}).items():
            if data["avg"] < 3.0 and data["count"] >= 5:
                alerts.append({
                    "type": "low_category_score",
                    "severity": "medium",
                    "message": f"Category '{cat}' has low avg score: {data['avg']:.2f}"
                })

        return {
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat()
            },
            "total_evaluations": metrics["total_evaluations"],
            "avg_score": avg_score,
            "score_distribution": metrics.get("score_distribution", {}),
            "alerts": alerts,
            "low_scoring_count": len(metrics.get("low_scoring_queries", []))
        }


def report_to_dict(report: DiagnosisReport) -> Dict[str, Any]:
    """Convert DiagnosisReport to dictionary for JSON serialization."""
    return {
        "generated_at": report.generated_at.isoformat(),
        "period_start": report.period_start.isoformat(),
        "period_end": report.period_end.isoformat(),
        "total_evaluations": report.total_evaluations,
        "avg_score": report.avg_score,
        "issues": [asdict(i) for i in report.issues],
        "actions": [asdict(a) for a in report.actions],
        "summary": report.summary
    }
