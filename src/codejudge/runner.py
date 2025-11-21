"""Execute candidates out-of-process and collect :class:`RunResult` objects."""
from __future__ import annotations

import json
import os
import subprocess
import sys

from .models import Candidate, CaseResult, RunResult, Task

_WORKER = os.path.join(os.path.dirname(__file__), "_worker.py")


def _all_failed(task: Task, error: str, runtime_ms: float = 0.0) -> list:
    return [
        CaseResult(name=c.name, passed=False, runtime_ms=runtime_ms, error=error)
        for c in task.cases
    ]


def run_candidate(
    task: Task,
    candidate: Candidate,
    python_exe: str = sys.executable,
) -> RunResult:
    """Run ``candidate`` against every case in ``task`` in a fresh subprocess.

    A single wall-clock timeout guards against infinite loops. If it trips we
    cannot attribute the hang to a specific case, so the whole run is marked
    crashed. Compile errors and a missing entrypoint are likewise treated as a
    crash with every case failing.
    """
    spec = {
