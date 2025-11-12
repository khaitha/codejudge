import os

import pytest

from codejudge.loader import load_candidates, load_task

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "two_sum")


def test_load_task_fields():
    task = load_task(EXAMPLE)
    assert task.id == "two-sum"
    assert task.entrypoint == "two_sum"
    assert len(task.cases) == 5
    assert task.weights.correctness == 0.6
    assert "indices" in task.prompt


def test_load_candidates():
    candidates = load_candidates(EXAMPLE)
    ids = {c.id for c in candidates}
    assert "optimal_hashmap" in ids
    assert "brute_force" in ids
    assert len(candidates) == 4
