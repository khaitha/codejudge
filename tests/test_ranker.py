from codejudge.models import CaseResult, QualityMetrics, RunResult, Task, TestCase
from codejudge.ranker import rank


def _run(cid, passed, total, runtime_ms=1.0):
    cases = [
        CaseResult(name=f"c{i}", passed=(i < passed), runtime_ms=runtime_ms)
        for i in range(total)
    ]
    return RunResult(candidate_id=cid, case_results=cases)


def _quality(score):
    return QualityMetrics(
        loc=5,
        cyclomatic=1,
        max_function_complexity=1,
        has_docstring=True,
        syntax_ok=True,
        score=score,
    )


def _task(n_cases):
    return Task(
        id="t",
        prompt="",
        entrypoint="f",
        cases=[TestCase(name=f"c{i}") for i in range(n_cases)],
    )


