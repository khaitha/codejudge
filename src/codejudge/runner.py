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
        "code": candidate.code,
        "entrypoint": task.entrypoint,
        "cases": [
            {"name": c.name, "args": c.args, "kwargs": c.kwargs, "expected": c.expected}
            for c in task.cases
        ],
    }
    # Overall budget: per-case limit times case count, plus startup slack.
    timeout = max(1.0, task.time_limit_s * max(1, len(task.cases)) + 0.5)

    try:
        proc = subprocess.run(
            [python_exe, "-I", _WORKER],
            input=json.dumps(spec),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return RunResult(
            candidate_id=candidate.id,
            case_results=_all_failed(task, "timeout", runtime_ms=timeout * 1000.0),
            crashed=True,
            error=f"timed out after {timeout:.1f}s",
        )

    if not proc.stdout.strip():
        return RunResult(
            candidate_id=candidate.id,
            case_results=_all_failed(task, "worker produced no output"),
            crashed=True,
            error=(proc.stderr.strip() or "worker exited without output")[-500:],
        )

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return RunResult(
            candidate_id=candidate.id,
            case_results=_all_failed(task, "unparseable worker output"),
            crashed=True,
            error=(proc.stdout or proc.stderr)[-500:],
        )

    if "fatal" in payload:
        # Code failed to compile/import, or the entrypoint was missing.
        return RunResult(
            candidate_id=candidate.id,
            case_results=_all_failed(task, "import/compile error"),
            crashed=True,
            error=payload["fatal"].strip().splitlines()[-1],
        )

    case_results = [
        CaseResult(
            name=c["name"],
            passed=bool(c["passed"]),
            runtime_ms=float(c["runtime_ms"]),
            got=c.get("got", ""),
            error=c.get("error"),
        )
        for c in payload["results"]
    ]
    return RunResult(candidate_id=candidate.id, case_results=case_results)
