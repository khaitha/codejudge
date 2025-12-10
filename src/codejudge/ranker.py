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
