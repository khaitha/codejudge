"""Command-line interface: ``codejudge run <task>`` and ``codejudge show <task>``."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from typing import List, Optional

import yaml

from . import __version__
from .evaluator import evaluate_task
from .loader import load_candidates, load_task
from .models import ScoreWeights
from .report import render_leaderboard, render_preferences, to_dict, to_markdown

# Errors that represent bad user input (vs. a bug) and should exit 2 cleanly.
_USER_ERRORS = (ValueError, OSError, yaml.YAMLError)


def _parse_weights(spec: str) -> ScoreWeights:
    parts = spec.split(",")
    if len(parts) != 3:
        raise ValueError("--weights expects three comma-separated numbers: correctness,performance,quality")
    correctness, performance, quality = (float(p) for p in parts)
    return ScoreWeights(correctness=correctness, performance=performance, quality=quality)


def _run(args: argparse.Namespace) -> int:
    try:
        task = load_task(args.task)
        if args.weights:
            task = replace(task, weights=_parse_weights(args.weights))
        report = evaluate_task(args.task, python_exe=args.python, task=task)
    except _USER_ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

