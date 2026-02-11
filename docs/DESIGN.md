# Design notes

This document explains how `codejudge` is put together, the scoring methodology,
the execution/threat model, and the known limitations of each metric. It is meant
to be read alongside the source — every section points at the module that
implements it.

## Goals

1. **Deterministic ranking order.** The same task and candidates always produce
   the same *ranking order*. Correctness and quality scores are fully
   deterministic; the performance score carries small wall-clock timing noise
   (see the performance caveat), so individual aggregate values can wobble in the
   last few decimals between runs.
2. **Auditable.** Every score traces to a test result or a static metric, and
   every preference carries a one-line reason.
3. **Safe enough to run untrusted-ish code.** Process isolation + timeouts so a
   bad candidate can't take the harness down (see the threat model caveats).
4. **Small and readable.** One runtime dependency; each stage is a pure function.

## Architecture

```
loader.py      task.yaml + candidates/*.py  ->  Task, [Candidate]
runner.py      Task, Candidate              ->  RunResult     (spawns _worker.py)
_worker.py     JSON spec on stdin           ->  JSON results on stdout
scorer.py      candidate source             ->  QualityMetrics
ranker.py      [RunResult], {QualityMetrics}->  EvaluationReport (scores+ranks+prefs)
report.py      EvaluationReport             ->  text / markdown / dict
evaluator.py   path                         ->  EvaluationReport  (wires it together)
cli.py         argv                         ->  process exit code
```

All data structures live in `models.py` as frozen-or-plain dataclasses, so the
whole report serializes with `dataclasses.asdict` and is trivial to build in
tests.

### Data flow

`evaluate_task(path)` loads the task and candidates, runs each candidate
out-of-process, computes static quality for each, then hands everything to
`rank()`, which produces the final `EvaluationReport`.

## Execution model & threat model

Each candidate is executed by `runner.run_candidate`, which spawns:

```
python -I src/codejudge/_worker.py
```

- **`-I` (isolated mode)** ignores `PYTHONPATH` and the user site directory, and
  doesn't add the script's directory to `sys.path`, reducing accidental imports.
- The candidate's code, the entrypoint name, and the cases are passed as **JSON
  on stdin**; results come back as **JSON on stdout**. The parent never imports
  candidate code into its own interpreter.
- The worker **redirects the candidate's `stdout`** to an in-memory buffer so
  that anything it prints cannot corrupt the result payload.
- A single **wall-clock timeout** (`time_limit_s × n_cases + slack`) guards
  against infinite loops. If it trips, the run is marked `crashed` and every case
  is failed, because we cannot attribute the hang to a specific case.

Failure taxonomy:

| Situation | Result |
| --- | --- |
| Candidate returns wrong value | case `passed=False`, run **not** crashed |
| Candidate raises at runtime | case `passed=False` with `error`, run **not** crashed |
| Compile/syntax error | run `crashed=True`, all cases failed |
| Missing/non-callable entrypoint | run `crashed=True`, all cases failed |
| Timeout | run `crashed=True`, all cases failed, `error="timed out…"` |

**This is process isolation, not a security sandbox.** The candidate runs with
the invoking user's permissions and can read/write files and open sockets.
`-I` and the subprocess boundary stop accidents and contain crashes; they do not
stop deliberately malicious code. For untrusted input, run the worker inside a
container, a seccomp profile, or a disposable VM. This is called out in the
README on purpose rather than hidden.

## Scoring methodology

All three dimensions are normalized to `[0, 1]`; the aggregate is the
weight-normalized sum (`ranker.rank`).

### Correctness (`ranker.rank`)

`n_passed / n_total`. Simple and decisive; with the default weights it dominates
the ranking, which is the right default for code evaluation.

### Performance (`ranker._performance_scores`)

Relative speed, measured as **average wall-clock per *passing* case**:

```
perf(c) = min_runtime_per_case / runtime_per_case(c)
```

so the fastest correct candidate gets `1.0` and a candidate twice as slow gets
`0.5`. Measuring over passing cases only means a candidate is never rewarded for
quickly producing wrong answers.

> **Known limitation.** Because the average is taken over the cases a candidate
> *passed*, a candidate that only passes the cheap cases can post a high `perf`
> score (in the bundled `two_sum` example, `buggy_offbyone` shows `perf = 1.00`
> because it only clears the small cases and never runs the expensive one). This
> is why correctness is weighted highest: the aggregate still ranks the buggy
> candidate well below the correct ones. A future version could score perf only
> over the set of cases that *all* candidates passed.

