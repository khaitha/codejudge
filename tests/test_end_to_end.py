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


