import os

import pytest

from codejudge import evaluate_task

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def test_two_sum_optimal_wins_and_crash_loses():
    report = evaluate_task(os.path.join(EXAMPLES, "two_sum"))

    ranking = [r.candidate_id for r in report.reports]
    # The O(n) solution should top the board (correct + fast + clean).
    assert ranking[0] == "optimal_hashmap"

    by_id = {r.candidate_id: r for r in report.reports}

    # Brute force is correct but slower than the hashmap.
    assert by_id["brute_force"].scores.correctness == 1.0
    assert by_id["optimal_hashmap"].scores.performance >= by_id["brute_force"].scores.performance

    # The off-by-one bug fails the case that needs the final index.
    assert by_id["buggy_offbyone"].scores.correctness < 1.0

    # The IndexError candidate raises on every case: zero correctness, ranks last.
    crasher = by_id["crashes_indexerror"]
    assert crasher.scores.correctness == 0.0
    assert all(c.error for c in crasher.run.case_results)
    assert ranking[-1] == "crashes_indexerror"


def test_two_sum_preferences_are_complete_and_consistent():
    report = evaluate_task(os.path.join(EXAMPLES, "two_sum"))
    n = len(report.reports)
    assert len(report.preferences) == n * (n - 1) // 2
    # Every preference's winner outranks its loser.
    rank_of = {r.candidate_id: r.rank for r in report.reports}
    for pref in report.preferences:
        assert rank_of[pref.winner] < rank_of[pref.loser]
        assert pref.margin >= 0


def test_is_anagram_buggy_length_check_is_not_top():
    report = evaluate_task(os.path.join(EXAMPLES, "is_anagram"))
    by_id = {r.candidate_id: r for r in report.reports}
    assert by_id["buggy_length_only"].scores.correctness < 1.0
    assert report.reports[0].candidate_id in {"optimal_counter", "sorted_compare"}


def test_custom_weights_change_outcome():
    from dataclasses import replace

    from codejudge.loader import load_task
    from codejudge.models import ScoreWeights

    base = load_task(os.path.join(EXAMPLES, "two_sum"))
    quality_only = replace(base, weights=ScoreWeights(0.0, 0.0, 1.0))
    report = evaluate_task(os.path.join(EXAMPLES, "two_sum"), task=quality_only)
    # Under quality-only weighting the crash candidate can't win.
    assert report.reports[0].candidate_id != "crashes_indexerror"


def test_missing_candidates_raises(tmp_path):
    from codejudge.loader import load_task

    task = load_task(os.path.join(EXAMPLES, "two_sum"))
    # tmp_path is an empty directory: a valid task but no candidate files.
    with pytest.raises(ValueError):
        evaluate_task(str(tmp_path), task=task)
