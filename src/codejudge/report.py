"""Render an :class:`EvaluationReport` as text, Markdown, or a JSON-able dict."""
from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Optional

from .models import EvaluationReport


def render_leaderboard(report: EvaluationReport) -> str:
    """A compact, aligned, plain-text leaderboard (zero dependencies)."""
    header = (
        f"{'#':>2}  {'candidate':<18} {'pass':>7}  "
        f"{'correct':>7} {'perf':>6} {'qual':>6}  {'score':>6}"
    )
    lines = [f"Task: {report.task_id}", header, "-" * len(header)]
    for cr in report.reports:
        passed = f"{cr.run.n_passed}/{cr.run.n_total}"
        flag = " !" if cr.run.crashed else ""
        lines.append(
            f"{cr.rank:>2}  {cr.candidate_id:<18} {passed:>7}  "
            f"{cr.scores.correctness:>7.2f} {cr.scores.performance:>6.2f} "
            f"{cr.scores.quality:>6.2f}  {cr.scores.aggregate:>6.3f}{flag}"
        )
    return "\n".join(lines)


def render_preferences(report: EvaluationReport, limit: Optional[int] = None) -> str:
    """Render the pairwise preference judgments (the RLHF-style output)."""
    prefs = report.preferences if limit is None else report.preferences[:limit]
    lines = ["Pairwise preferences (RLHF-style):"]
    for p in prefs:
        lines.append(f"  {p.winner}  >  {p.loser}   (delta {p.margin:.3f})  - {p.reason}")
    if limit is not None and len(report.preferences) > limit:
