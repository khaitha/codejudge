"""Static quality scoring of candidate source code (no execution required).

The score is a transparent, documented heuristic — not a verdict on taste. It
rewards low control-flow complexity, the presence of a docstring, and concise
solutions, because those correlate with code that is easy to review (the actual
job a code-evaluation Fellow does). The exact formula lives in
:func:`_quality_score` and is described in ``docs/DESIGN.md``.
"""
from __future__ import annotations

import ast
from typing import List

from .models import QualityMetrics

# AST node types that each introduce one extra control-flow branch.
_BRANCH_NODES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.With,
    ast.AsyncWith,
    ast.Assert,
    ast.IfExp,
)


def _count_logical_loc(source: str) -> int:
    """Lines of code, ignoring blanks and whole-line comments."""
    loc = 0
    for line in source.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            loc += 1
    return loc

