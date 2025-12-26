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

