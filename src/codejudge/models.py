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


@dataclass(frozen=True)
class Task:
    """A coding problem plus the tests and scoring policy used to judge it."""

    id: str
    prompt: str
    entrypoint: str
    cases: List[TestCase]
    time_limit_s: float = 2.0
    weights: ScoreWeights = field(default_factory=ScoreWeights)


@dataclass(frozen=True)
class Candidate:
    """One AI-generated (or human) solution to a :class:`Task`."""

    id: str
    code: str
    source_path: Optional[str] = None


@dataclass
class CaseResult:
    """Outcome of running a single :class:`TestCase` against a candidate."""

    name: str
    passed: bool
    runtime_ms: float
    got: str = ""
    error: Optional[str] = None


@dataclass
class RunResult:
    """All case outcomes for one candidate, plus any fatal-crash signal."""

    candidate_id: str
    case_results: List[CaseResult] = field(default_factory=list)
    crashed: bool = False
    error: Optional[str] = None

    @property
    def n_total(self) -> int:
        return len(self.case_results)

    @property
    def n_passed(self) -> int:
        return sum(1 for c in self.case_results if c.passed)

    @property
    def passed_runtime_ms(self) -> float:
        """Total wall-clock over the cases that passed (used for perf scoring)."""
        return sum(c.runtime_ms for c in self.case_results if c.passed)


@dataclass
class QualityMetrics:
    """Static (no-execution) source-quality signals for a candidate."""

    loc: int
    cyclomatic: int
    max_function_complexity: int
    has_docstring: bool
    syntax_ok: bool
    score: float  # normalized to 0..1


@dataclass
class ScoreBreakdown:
    """The three dimension scores plus their weighted aggregate (all 0..1)."""

    correctness: float
    performance: float
    quality: float
    aggregate: float


@dataclass
class CandidateReport:
    """Everything known about one candidate after evaluation."""

    candidate_id: str
    run: RunResult
    quality: QualityMetrics
    scores: ScoreBreakdown
    rank: int = 0


@dataclass
class Preference:
    """A pairwise preference judgment — the unit of RLHF-style training data."""

    winner: str
    loser: str
    margin: float
    reason: str


@dataclass
class EvaluationReport:
    """The full result of evaluating a task: ranked reports + preferences."""

    task_id: str
    reports: List[CandidateReport]
    preferences: List[Preference] = field(default_factory=list)
