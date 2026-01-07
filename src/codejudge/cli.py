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

    print(render_leaderboard(report))
    print()
    print(render_preferences(report, limit=args.max_prefs))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(to_dict(report), fh, indent=2)
        print(f"\nWrote JSON report to {args.json}")
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(report))
        print(f"Wrote Markdown report to {args.markdown}")
    return 0


def _show(args: argparse.Namespace) -> int:
    try:
        task = load_task(args.task)
        candidates = load_candidates(args.task)
    except _USER_ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Task: {task.id}")
    print(f"Entrypoint: {task.entrypoint}()   time limit: {task.time_limit_s}s")
    print(
        f"Weights: correctness={task.weights.correctness}, "
        f"performance={task.weights.performance}, quality={task.weights.quality}"
    )
    print(f"Cases: {len(task.cases)}")
    print(f"Candidates: {', '.join(c.id for c in candidates) or '(none)'}")
    if task.prompt:
        print(f"\nPrompt:\n{task.prompt}")
    return 0


