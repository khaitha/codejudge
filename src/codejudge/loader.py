"""Load tasks and candidate solutions from disk.

A task is a directory shaped like::

    my_task/
      task.yaml            # problem prompt, entrypoint, cases, weights
      candidates/
        model_a.py         # each .py file defines the entrypoint function
        model_b.py

The candidate id is the file stem (``model_a``), which is what shows up on the
leaderboard.
"""
from __future__ import annotations

import os
from typing import List

import yaml

from .models import Candidate, ScoreWeights, Task, TestCase


def load_task(path: str) -> Task:
    """Load a :class:`Task` from a task directory or a ``task.yaml`` file."""
    config_path = os.path.join(path, "task.yaml") if os.path.isdir(path) else path
    with open(config_path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"{config_path}: task file is empty or not a YAML mapping")
    for required in ("id", "entrypoint"):
        if required not in data:
            raise ValueError(f"{config_path}: missing required key {required!r}")

    cases = [
        TestCase(
            name=c["name"],
            args=c.get("args", []),
            kwargs=c.get("kwargs", {}),
            expected=c.get("expected"),
        )
        for c in data.get("cases", [])
    ]

    weights_data = data.get("weights") or {}
    weights = ScoreWeights(
        correctness=weights_data.get("correctness", 0.6),
        performance=weights_data.get("performance", 0.25),
        quality=weights_data.get("quality", 0.15),
    )

    return Task(
        id=data["id"],
        prompt=str(data.get("prompt", "")).strip(),
        entrypoint=data["entrypoint"],
        cases=cases,
        time_limit_s=float(data.get("time_limit_s", 2.0)),
        weights=weights,
    )


def load_candidates(path: str) -> List[Candidate]:
    """Load every ``.py`` file under ``<task>/candidates`` as a candidate.

    Files beginning with ``_`` are skipped so helpers don't get judged.
    """
    if os.path.isdir(path):
        candidates_dir = os.path.join(path, "candidates")
        if not os.path.isdir(candidates_dir):
            candidates_dir = path
    else:
        candidates_dir = os.path.dirname(path)

    candidates: List[Candidate] = []
    for filename in sorted(os.listdir(candidates_dir)):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue
        file_path = os.path.join(candidates_dir, filename)
        with open(file_path, "r", encoding="utf-8") as fh:
            code = fh.read()
        candidates.append(
            Candidate(id=os.path.splitext(filename)[0], code=code, source_path=file_path)
        )
    return candidates
