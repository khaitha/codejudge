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

