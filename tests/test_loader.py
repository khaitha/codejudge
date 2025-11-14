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
    for candidate in candidates:
        assert candidate.code.strip()
        assert candidate.source_path is not None


def test_weights_normalize_to_one():
    task = load_task(EXAMPLE)
    normalized = task.weights.normalized()
    total = normalized.correctness + normalized.performance + normalized.quality
    assert abs(total - 1.0) < 1e-9


def test_empty_task_file_raises_valueerror(tmp_path):
    bad = tmp_path / "task.yaml"
    bad.write_text("")
    with pytest.raises(ValueError):
        load_task(str(tmp_path))


def test_missing_required_key_raises_valueerror(tmp_path):
    bad = tmp_path / "task.yaml"
    bad.write_text("prompt: hi\ncases: []\n")  # no id / entrypoint
    with pytest.raises(ValueError):
        load_task(str(tmp_path))
