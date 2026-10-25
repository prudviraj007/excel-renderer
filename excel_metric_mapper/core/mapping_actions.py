"""Helpers for mapping review, selection, and bulk actions."""
from __future__ import annotations

from typing import Iterable, List, Optional

from .models import MappingCandidate, SourceMetric


def candidate_key(candidate: MappingCandidate) -> str:
    return (
        f"{candidate.workbook_name}|{candidate.sheet_name}|"
        f"{candidate.metric_id}|{candidate.target_value_cell}"
    )


def group_key(candidate: MappingCandidate) -> str:
    """One winner per workbook + metric for the reporting month."""
    return f"{candidate.workbook_name}|{candidate.metric_id}"


def filter_candidates(
    candidates: Iterable[MappingCandidate],
    *,
    states: Optional[List[str]] = None,
    workbooks: Optional[List[str]] = None,
    metric_ids: Optional[List[str]] = None,
    min_confidence: float = 0.0,
) -> List[MappingCandidate]:
    result = list(candidates)
    if states:
        result = [c for c in result if c.state in states]
    if workbooks:
        result = [c for c in result if c.workbook_name in workbooks]
    if metric_ids:
        result = [c for c in result if c.metric_id in metric_ids]
    return [c for c in result if c.confidence >= min_confidence]


def set_winner(candidates: List[MappingCandidate], winner: MappingCandidate) -> None:
    """Approve one candidate and reject other targets for the same workbook + metric."""
    gk = group_key(winner)
    winner_key = candidate_key(winner)
    for c in candidates:
        if group_key(c) != gk:
            continue
        if candidate_key(c) == winner_key:
            c.state = "approved"
        elif c.state in ("suggested", "ambiguous", "approved"):
            c.state = "rejected"


def bulk_approve_high_confidence(
    candidates: List[MappingCandidate],
    threshold: float = 0.8,
) -> int:
    """Approve the best non-formula candidate per workbook+metric if it meets threshold."""
    by_group: dict[str, List[MappingCandidate]] = {}
    for c in candidates:
        if c.has_formula or c.state == "blocked":
            continue
        by_group.setdefault(group_key(c), []).append(c)

    count = 0
    for group in by_group.values():
        eligible = [c for c in group if c.state in ("suggested", "ambiguous")]
        if not eligible:
            continue
        best = max(eligible, key=lambda x: x.confidence)
        if best.confidence < threshold:
            continue
        set_winner(candidates, best)
        count += 1
    return count


def bulk_reject_ambiguous(candidates: List[MappingCandidate]) -> int:
    count = 0
    for c in candidates:
        if c.state == "ambiguous":
            c.state = "rejected"
            count += 1
    return count


def target_metrics_for_month(
    source_metrics: List[SourceMetric],
    target_month: str,
) -> List[SourceMetric]:
    return [m for m in source_metrics if m.reporting_month == target_month]


def coverage_summary(
    source_metrics: List[SourceMetric],
    candidates: List[MappingCandidate],
    target_month: str,
) -> List[dict]:
    """Per-metric status for the mapping board."""
    metrics = target_metrics_for_month(source_metrics, target_month)
    rows = []
    for m in metrics:
        related = [c for c in candidates if c.metric_id == m.metric_id]
        approved = [c for c in related if c.state == "approved"]
        pending = [c for c in related if c.state in ("suggested", "ambiguous")]
        rows.append(
            {
                "metric_id": m.metric_id,
                "metric_name": m.metric_name,
                "source_value": m.value,
                "unit": m.unit,
                "candidates": len(related),
                "approved": len(approved),
                "pending": len(pending),
                "status": (
                    "✅ Mapped"
                    if approved
                    else ("⚠️ Review" if pending else "❌ No match")
                ),
            }
        )
    return rows
