"""High-level entry point that wires the pipeline stages together.

    load -> run (per candidate) -> score quality -> rank -> report

Kept separate from the CLI so the harness is usable as a library:

    from codejudge import evaluate_task
    report = evaluate_task("examples/two_sum")
    print(report.reports[0].candidate_id)
"""
from __future__ import annotations

import sys
from typing import Optional

from .loader import load_candidates, load_task
from .models import EvaluationReport, Task
from .ranker import rank
from .runner import run_candidate
from .scorer import analyze_quality


def evaluate_task(
    path: str,
    python_exe: str = sys.executable,
    task: Optional[Task] = None,
) -> EvaluationReport:
    """Evaluate every candidate of the task at ``path`` and return the report.

    Pass ``task`` to override the on-disk task config (e.g. with custom weights);
    candidates are still loaded from ``path``.
    """
    task = task or load_task(path)
    candidates = load_candidates(path)
    if not candidates:
        raise ValueError(f"No candidate solutions found under {path!r}")

    runs = [run_candidate(task, c, python_exe=python_exe) for c in candidates]
    qualities = {c.id: analyze_quality(c.code) for c in candidates}
    return rank(task, runs, qualities)
