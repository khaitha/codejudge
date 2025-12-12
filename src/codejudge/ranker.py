"""Aggregate per-candidate signals into scores, a ranking, and preferences.

This is the heart of the harness: it turns raw run results and quality metrics
into (a) a normalized 0..1 score per dimension, (b) a weighted aggregate, (c) a
total ordering, and (d) pairwise preference judgments — the same shape as the
human-preference data used to train reward models in RLHF.
"""
from __future__ import annotations

from typing import Dict, List

from .models import (
    CandidateReport,
    EvaluationReport,
    Preference,
    QualityMetrics,
    RunResult,
    ScoreBreakdown,
    Task,
)


def _performance_scores(runs: List[RunResult]) -> Dict[str, float]:
    """Relative speed in [0, 1]; the fastest correct candidate scores 1.0.

    Speed is measured as average wall-clock per *passing* case, so a candidate
    is never rewarded for being fast at producing wrong answers. Candidates with
    no passing cases score 0.0.
    """
    best: float = float("inf")
    for r in runs:
        if r.n_passed > 0:
            best = min(best, r.passed_runtime_ms / r.n_passed)

    scores: Dict[str, float] = {}
    for r in runs:
        if r.n_passed == 0 or best == float("inf"):
            scores[r.candidate_id] = 0.0
        else:
            avg = r.passed_runtime_ms / r.n_passed
            scores[r.candidate_id] = 1.0 if avg <= 0 else min(1.0, best / avg)
    return scores


def _explain(winner: CandidateReport, loser: CandidateReport, margin: float) -> str:
    """One-line rationale naming the dimension the winner leads on most."""
    diffs = {
        "correctness": winner.scores.correctness - loser.scores.correctness,
        "performance": winner.scores.performance - loser.scores.performance,
        "quality": winner.scores.quality - loser.scores.quality,
    }
    dim = max(diffs, key=lambda k: diffs[k])
    lead = diffs[dim]
    if lead <= 1e-9:
        return (
            f"{winner.candidate_id} edges out {loser.candidate_id} on aggregate "
            f"(+{margin:.3f}); dimensions near-identical"
        )
    return (
        f"{winner.candidate_id} preferred over {loser.candidate_id}: stronger "
        f"{dim} (+{lead:.2f}); aggregate +{margin:.3f}"
    )


def _preferences(reports: List[CandidateReport]) -> List[Preference]:
    """Full pairwise preferences implied by the ranking (winner ranks above loser)."""
    prefs: List[Preference] = []
    for i in range(len(reports)):
        for j in range(i + 1, len(reports)):
            winner, loser = reports[i], reports[j]
            margin = winner.scores.aggregate - loser.scores.aggregate
            prefs.append(
                Preference(
                    winner=winner.candidate_id,
                    loser=loser.candidate_id,
                    margin=margin,
                    reason=_explain(winner, loser, margin),
                )
            )
    return prefs


def rank(
    task: Task,
    runs: List[RunResult],
    qualities: Dict[str, QualityMetrics],
) -> EvaluationReport:
    """Score, rank, and derive preferences for all candidates of a task."""
    weights = task.weights.normalized()
    performance = _performance_scores(runs)

