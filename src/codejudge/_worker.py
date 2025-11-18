"""Out-of-process execution worker.

Runs ONE candidate's code against a list of cases inside an isolated subprocess
(launched by :mod:`codejudge.runner` with ``python -I``). It communicates purely
via JSON on stdin/stdout, so the parent process is insulated from crashes, stray
``print`` output, and most misbehavior in candidate code.

This is *process isolation with a wall-clock timeout* enforced by the parent — it
is deliberately NOT a security sandbox. See ``docs/DESIGN.md`` for the threat
model and its limitations.
"""
from __future__ import annotations

import io
import json
import sys
import time
import traceback


def _safe_repr(value: object, limit: int = 200) -> str:
    try:
        text = repr(value)
    except Exception:
        text = "<unreprable>"
    return text if len(text) <= limit else text[:limit] + "..."


def _evaluate(spec: dict) -> dict:
    """Compile the candidate, run every case, and return a JSON-able result.

    Candidate stdout is redirected to an in-memory buffer by the caller so that
    anything the candidate prints cannot corrupt our result payload.
    """
    code = spec["code"]
    entrypoint = spec["entrypoint"]
    cases = spec["cases"]

    namespace: dict = {}
    try:
        compiled = compile(code, "<candidate>", "exec")
        exec(compiled, namespace)
    except Exception:
        return {"fatal": traceback.format_exc(limit=3)}

