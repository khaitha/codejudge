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

    fn = namespace.get(entrypoint)
    if not callable(fn):
        return {"fatal": f"entrypoint {entrypoint!r} is not defined or not callable"}

    results = []
    for case in cases:
        args = case.get("args", [])
        kwargs = case.get("kwargs", {})
        expected = case.get("expected")
        start = time.perf_counter()
        try:
            got = fn(*args, **kwargs)
            runtime_ms = (time.perf_counter() - start) * 1000.0
            results.append(
                {
                    "name": case["name"],
                    "passed": got == expected,
                    "runtime_ms": runtime_ms,
                    "got": _safe_repr(got),
                }
            )
        except Exception:
            runtime_ms = (time.perf_counter() - start) * 1000.0
            last_line = traceback.format_exc(limit=2).strip().splitlines()[-1]
            results.append(
                {
                    "name": case["name"],
                    "passed": False,
                    "runtime_ms": runtime_ms,
                    "error": last_line,
                }
            )
    return {"results": results}


def main() -> None:
    spec = json.load(sys.stdin)
    real_stdout = sys.stdout
    # Quarantine anything the candidate prints so it can't pollute our payload.
    sys.stdout = io.StringIO()
    try:
        payload = _evaluate(spec)
    finally:
        sys.stdout = real_stdout
    json.dump(payload, real_stdout)


if __name__ == "__main__":
    main()
