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


def _branch_count(node: ast.AST) -> int:
    """Approximate the extra decision points within ``node``'s subtree."""
    count = 0
    for child in ast.walk(node):
        if isinstance(child, _BRANCH_NODES):
            count += 1
        elif isinstance(child, ast.BoolOp):
            # `a and b and c` adds two decision points beyond the base path.
            count += len(child.values) - 1
        elif isinstance(child, ast.comprehension):
            count += len(child.ifs)
    return count


def _quality_score(loc: int, max_fn_complexity: int, has_docstring: bool) -> float:
    """Combine the raw metrics into a single 0..1 score.

    * complexity (weight 0.6): 1.0 at complexity 1, decaying as branches grow.
    * docstring  (weight 0.2): full marks with a docstring, 0.6 without.
    * brevity    (weight 0.2): full marks up to ~25 logical lines, then decays.
    """
    complexity_sub = 1.0 / (1.0 + max(0, max_fn_complexity - 1) / 8.0)
    docstring_sub = 1.0 if has_docstring else 0.6
    brevity_sub = 1.0 / (1.0 + max(0, loc - 25) / 50.0)
    score = 0.6 * complexity_sub + 0.2 * docstring_sub + 0.2 * brevity_sub
    return max(0.0, min(1.0, score))


def analyze_quality(source: str) -> QualityMetrics:
    """Return static :class:`QualityMetrics` for a candidate's source code."""
    loc = _count_logical_loc(source)
    if loc == 0:
        # Empty or comments-only file: parses fine, but there is no code to praise.
        return QualityMetrics(
            loc=0,
            cyclomatic=0,
