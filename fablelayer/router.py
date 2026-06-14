"""FL3/FL4 Smart Model Router.

모델 capability는 하네스로 전이되지 않는다. 라우터는 작업 신호에 따라
모델 등급(sonnet/opus)을 선택할 뿐, 선택된 모델의 능력을 다른 모델로
옮기지 못한다. 모든 RouteDecision.note 가 이 한계를 명시한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

DEFAULT_MODEL = "sonnet"
ESCALATED_MODEL = "opus"
CAPABILITY_NOTE = "capability not transferable"

# 신호 임계값 (INTERFACE 계약)
DEP_DEPTH_THRESHOLD = 3
FILES_TOUCHED_THRESHOLD = 3
CONTEXT_PCT_THRESHOLD = 0.8
GATE_FAILURES_THRESHOLD = 2


@dataclass(frozen=True)
class TaskSpec:
    kind: str
    dependency_depth: int = 0
    files_touched: int = 0
    deep_reasoning: bool = False
    context_pct: float = 0.0
    gate_failures: int = 0
    explicit_opus: bool = False


@dataclass(frozen=True)
class RouteDecision:
    model: str
    fired_signals: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class _Signal:
    name: str
    predicate: Callable[[TaskSpec], bool]


# 6 escalation predicates — 발화 시 opus 로 상향
ESCALATION_SIGNALS: tuple[_Signal, ...] = (
    _Signal("dep_depth>=3", lambda t: t.dependency_depth >= DEP_DEPTH_THRESHOLD),
    _Signal("deep_reasoning", lambda t: bool(t.deep_reasoning)),
    _Signal("files>=3", lambda t: t.files_touched >= FILES_TOUCHED_THRESHOLD),
    _Signal("context_pct>=0.8", lambda t: t.context_pct >= CONTEXT_PCT_THRESHOLD),
    _Signal("gate_failures>=2", lambda t: t.gate_failures >= GATE_FAILURES_THRESHOLD),
    _Signal("explicit_opus", lambda t: bool(t.explicit_opus)),
)


def _fired_signals(task: TaskSpec) -> tuple[str, ...]:
    """발화한 신호 이름을 ESCALATION_SIGNALS 순서대로 결정론적으로 반환한다."""
    return tuple(sig.name for sig in ESCALATION_SIGNALS if sig.predicate(task))


def route(task: TaskSpec) -> RouteDecision:
    """기본 sonnet. 신호가 하나라도 발화하면 opus.

    explicit_opus 는 비강등(다른 신호 유무와 무관하게 opus 유지).
    note 는 항상 'capability not transferable' 을 포함한다.
    """
    fired = _fired_signals(task)

    if fired:
        model = ESCALATED_MODEL
        reason = "escalated to opus by: " + ", ".join(fired)
    else:
        model = DEFAULT_MODEL
        reason = "default sonnet; no escalation signal fired"

    note = f"{reason}. {CAPABILITY_NOTE}: routing selects model tier, it does not transfer capability across models."
    return RouteDecision(model=model, fired_signals=fired, note=note)
