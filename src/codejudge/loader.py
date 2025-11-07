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
