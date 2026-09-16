from __future__ import annotations

from typing import Any

from .base import (
    StrategyOutcome,
    TaskStrategy,
    location_xyz,
    object_aabb,
    object_size,
    subject_identity,
    task_type_of,
)
from .counting import CountingStrategy
from .jigsaw import JigsawStrategy
from .raven import RavenStrategy
from .tidyroom import TidyRoomGuard

__all__ = [
    "CountingStrategy",
    "JigsawStrategy",
    "RavenStrategy",
    "StrategyOutcome",
    "TaskStrategy",
    "TidyRoomGuard",
    "build_strategy",
    "location_xyz",
    "object_aabb",
    "object_size",
    "subject_identity",
    "task_type_of",
]

_STRATEGY_REGISTRY: dict[str, type[TaskStrategy]] = {
    "counting": CountingStrategy,
    "jigsaw": JigsawStrategy,
    "raven": RavenStrategy,
}


def build_strategy(task_type: str, agent: Any) -> TaskStrategy | None:
    """Create the strategy for a task type, or None for the generic VLM path."""

    strategy_cls = _STRATEGY_REGISTRY.get(str(task_type or "").strip().lower())
    if strategy_cls is None:
        return None
    return strategy_cls(agent)
