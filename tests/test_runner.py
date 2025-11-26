from codejudge.models import Candidate, Task, TestCase
from codejudge.runner import run_candidate


def _task(entry="solve", cases=None, time_limit_s=1.0):
    return Task(
        id="t",
        prompt="",
        entrypoint=entry,
        cases=cases or [TestCase(name="c1", args=[2], expected=4)],
        time_limit_s=time_limit_s,
    )


def test_correct_candidate_passes():
    task = _task(cases=[TestCase(name="square", args=[3], expected=9)])
    cand = Candidate(id="ok", code="def solve(x):\n    return x * x\n")
    result = run_candidate(task, cand)
    assert not result.crashed
    assert result.n_passed == 1
    assert result.case_results[0].runtime_ms >= 0.0


def test_wrong_answer_fails_without_crash():
    task = _task(cases=[TestCase(name="square", args=[3], expected=9)])
    cand = Candidate(id="bad", code="def solve(x):\n    return x + x\n")
    result = run_candidate(task, cand)
    assert result.n_passed == 0
    assert not result.crashed  # it ran fine, it was just wrong
    assert result.case_results[0].got == "6"


