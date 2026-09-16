from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class StrategyOutcome:
    """One step result produced by a task strategy.

    Exactly one of ``action``, ``payload`` or ``finish`` is normally set.
    ``action`` is executed through ``VLMAgent._do_action``; ``payload`` is
    reported to the task server as-is; ``finish`` sends the standard finish
    action. Returning ``None`` falls back to the generic VLM loop.
    """

    action: dict[str, Any] | None = None
    payload: dict[str, Any] | None = None
    finish: bool = False
    note: str = ""

    @classmethod
    def from_action(cls, action: dict[str, Any], note: str = "") -> "StrategyOutcome":
        return cls(action=action, note=note)

    @classmethod
    def from_payload(cls, payload: dict[str, Any], note: str = "") -> "StrategyOutcome":
        return cls(payload=payload, note=note)

    @classmethod
    def finished(cls, note: str = "") -> "StrategyOutcome":
        return cls(finish=True, note=note)


class TaskStrategy:
    """Base class for deterministic per-task controllers."""

    name = "base"

    def __init__(self, agent: Any) -> None:
        self.agent = agent

    def can_handle(self, subject: Any) -> bool:
        return True

    def reset(self, subject: Any) -> None:
        """Reset per-subject state. Called when the subject identity changes."""

    def step(
        self,
        subject: Any,
        task_response: dict[str, Any] | None = None,
    ) -> StrategyOutcome | None:
        return None

    def summary(self) -> dict[str, Any]:
        return {}


def task_type_of(subject: Any) -> str:
    if not isinstance(subject, dict):
        return ""
    return str(subject.get("task_type") or "").strip().lower()


def subject_text(subject: Any) -> str:
    if not isinstance(subject, dict):
        return ""
    for key in ("subject", "question", "task_prompt", "goal"):
        value = subject.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def subject_identity(subject: Any) -> str:
    """Stable identity for one question/subject.

    The full subject dict is intentionally not hashed because some tasks
    attach per-step payloads (for example Raven images). Only fields that
    identify the question are used so a strategy keeps its state while the
    same question is retried.
    """

    payload = {
        "task_type": task_type_of(subject),
        "text": subject_text(subject),
        "options": subject.get("options") if isinstance(subject, dict) else None,
        "counting_type": subject.get("counting_type") if isinstance(subject, dict) else None,
        "stage": subject.get("stage") if isinstance(subject, dict) else None,
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.md5(blob.encode("utf-8")).hexdigest()


def location_xyz(value: Any) -> list[float] | None:
    if isinstance(value, dict):
        x = value.get("X", value.get("x"))
        y = value.get("Y", value.get("y"))
        z = value.get("Z", value.get("z"))
    elif isinstance(value, (list, tuple)) and len(value) >= 3:
        x, y, z = value[0], value[1], value[2]
    else:
        return None
    try:
        return [float(x), float(y), float(z)]
    except (TypeError, ValueError):
        return None


def object_aabb(obj: Any) -> tuple[float, float, float, float, float, float] | None:
    if not isinstance(obj, dict):
        return None
    aabb = obj.get("world_aabb")
    if not isinstance(aabb, dict):
        return None
    lo = aabb.get("min") or {}
    hi = aabb.get("max") or {}
    try:
        return (
            float(lo["x"]),
            float(lo["y"]),
            float(lo["z"]),
            float(hi["x"]),
            float(hi["y"]),
            float(hi["z"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def object_size(obj: Any) -> tuple[float, float, float]:
    box = object_aabb(obj)
    if box is None:
        return (0.0, 0.0, 0.0)
    return (abs(box[3] - box[0]), abs(box[4] - box[1]), abs(box[5] - box[2]))


def object_volume(obj: Any) -> float:
    sx, sy, sz = object_size(obj)
    return sx * sy * sz
