"""Core data structures for the codejudge evaluation pipeline.

Everything here is a plain dataclass so that results serialize cleanly to JSON
(via :func:`dataclasses.asdict`) and are trivial to construct in tests.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TestCase:
    """A single input/expected-output pair used to check correctness."""

    name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    expected: Any = None


# Tell pytest this domain class is not a test case to collect (its name matches
# the default ``Test*`` discovery pattern).
TestCase.__test__ = False


@dataclass(frozen=True)
class ScoreWeights:
    """Relative importance of each scoring dimension.

    The three weights need not sum to 1; they are normalized at aggregation
    time, so ``(6, 2.5, 1.5)`` and ``(0.6, 0.25, 0.15)`` mean the same thing.
    """

    correctness: float = 0.6
    performance: float = 0.25
    quality: float = 0.15

    def normalized(self) -> "ScoreWeights":
        total = self.correctness + self.performance + self.quality
        if total <= 0:
            raise ValueError("Score weights must sum to a positive number")
        return ScoreWeights(
            correctness=self.correctness / total,
            performance=self.performance / total,
            quality=self.quality / total,
        )


