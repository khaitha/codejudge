"""codejudge — a preference-ranking harness for evaluating AI-generated code.

Public API:

    from codejudge import evaluate_task
    report = evaluate_task("examples/two_sum")
"""
from __future__ import annotations

__version__ = "0.1.0"

from .evaluator import evaluate_task
from .models import (
    Candidate,
    CandidateReport,
    EvaluationReport,
    Preference,
    ScoreBreakdown,
    ScoreWeights,
    Task,
    TestCase,
)

