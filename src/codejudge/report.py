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
        lines.append(f"  ... and {len(report.preferences) - limit} more")
    return "\n".join(lines)


def to_markdown(report: EvaluationReport) -> str:
    """A self-contained Markdown report suitable for a PR comment or gist."""
    lines = [
        f"# Evaluation report: `{report.task_id}`",
        "",
        "## Leaderboard",
        "",
        "| Rank | Candidate | Pass | Correctness | Performance | Quality | **Score** |",
        "| ---: | --- | :---: | ---: | ---: | ---: | ---: |",
    ]
    for cr in report.reports:
        passed = f"{cr.run.n_passed}/{cr.run.n_total}"
        name = cr.candidate_id + (" ⚠️" if cr.run.crashed else "")
        lines.append(
            f"| {cr.rank} | `{name}` | {passed} | {cr.scores.correctness:.2f} | "
            f"{cr.scores.performance:.2f} | {cr.scores.quality:.2f} | "
            f"**{cr.scores.aggregate:.3f}** |"
        )

    lines += ["", "## Pairwise preferences", ""]
    for p in report.preferences:
        lines.append(f"- **{p.winner}** ≻ {p.loser} — {p.reason}")
    lines.append("")
    return "\n".join(lines)


def to_dict(report: EvaluationReport) -> Dict:
    """A plain dict (JSON-serializable) of the entire report."""
    return asdict(report)
