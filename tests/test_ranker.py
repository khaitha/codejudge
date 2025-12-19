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


def test_more_correct_ranks_higher():
    runs = [_run("a", 4, 4, runtime_ms=2.0), _run("b", 2, 4, runtime_ms=1.0)]
    qualities = {"a": _quality(0.5), "b": _quality(0.9)}
    report = rank(_task(4), runs, qualities)
    assert report.reports[0].candidate_id == "a"
    assert report.reports[0].rank == 1
    assert report.reports[1].rank == 2


def test_performance_favors_faster_when_correctness_ties():
    fast = _run("fast", 1, 1, runtime_ms=1.0)
    slow = _run("slow", 1, 1, runtime_ms=10.0)
    qualities = {"fast": _quality(0.8), "slow": _quality(0.8)}
    report = rank(_task(1), [slow, fast], qualities)
    assert report.reports[0].candidate_id == "fast"
    by_id = {r.candidate_id: r.scores.performance for r in report.reports}
    assert by_id["fast"] > by_id["slow"]
    assert by_id["fast"] == 1.0


def test_zero_passing_scores_zero_performance():
    report = rank(_task(2), [_run("none", 0, 2)], {"none": _quality(0.9)})
    assert report.reports[0].scores.performance == 0.0


def test_preferences_follow_ranking_order():
    runs = [_run("a", 1, 1, 1.0), _run("b", 0, 1, 1.0)]
    qualities = {"a": _quality(0.8), "b": _quality(0.8)}
    report = rank(_task(1), runs, qualities)
    assert len(report.preferences) == 1
    pref = report.preferences[0]
    assert pref.winner == "a"
    assert pref.loser == "b"
    assert pref.margin > 0
    assert "correctness" in pref.reason


def test_n_choose_2_preferences_generated():
    runs = [_run("a", 3, 3), _run("b", 2, 3), _run("c", 1, 3)]
    qualities = {cid: _quality(0.7) for cid in ("a", "b", "c")}
    report = rank(_task(3), runs, qualities)
    assert len(report.preferences) == 3  # 3 choose 2
