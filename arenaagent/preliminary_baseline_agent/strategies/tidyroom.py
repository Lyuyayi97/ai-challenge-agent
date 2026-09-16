from __future__ import annotations

from typing import Any

from .base import object_size, object_volume, subject_identity


class TidyRoomGuard:
    """Guardrails around the semantic tidy-room task.

    The perception payload exposes colour, shape and geometry but no object
    class name, so semantic classification stays with the VLM. This guard adds
    the state that natural language alone cannot guarantee: a failed-grab
    blacklist, per-object attempt limits and a hard finish condition.
    """

    MAX_ATTEMPTS_PER_OBJECT = 2
    MAX_CANDIDATES = 24

    def __init__(self) -> None:
        self._identity = ""
        self._attempts: dict[str, int] = {}
        self._failed: set[str] = set()
        self._placed: set[str] = set()
        self._picked: str = ""

    def begin(self, subject: Any) -> None:
        identity = subject_identity(subject)
        if identity == self._identity:
            return
        self._identity = identity
        self._attempts = {}
        self._failed = set()
        self._placed = set()
        self._picked = ""

    def can_attempt(self, object_id: Any) -> bool:
        key = str(object_id)
        return bool(key) and self._attempts.get(key, 0) < self.MAX_ATTEMPTS_PER_OBJECT

    def filter_objects(self, objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for obj in objects or []:
            if not isinstance(obj, dict):
                continue
            object_id = str(obj.get("object_id") or "")
            if not object_id or object_id in self._failed:
                continue
            if max(object_size(obj)) <= 0.01:
                continue
            candidates.append(obj)
        candidates.sort(key=object_volume)
        return candidates[: self.MAX_CANDIDATES]

    def record_take(self, object_id: Any, result: Any) -> bool:
        key = str(object_id or "")
        failed = isinstance(result, dict) and result.get("result") == "failed"
        if not key:
            return failed
        if failed:
            self._attempts[key] = self._attempts.get(key, 0) + 1
            if self._attempts[key] >= self.MAX_ATTEMPTS_PER_OBJECT:
                self._failed.add(key)
        else:
            self._picked = key
        return failed

    def record_place(self, object_id: Any, result: Any) -> bool:
        key = str(object_id or self._picked or "")
        failed = isinstance(result, dict) and result.get("result") == "failed"
        if not key:
            return failed
        if failed:
            return True
        self._placed.add(key)
        self._attempts.pop(key, None)
        if key == self._picked:
            self._picked = ""
        return False

    def can_finish(self, object_in_hand: Any) -> bool:
        if bool(object_in_hand):
            return False
        if self._picked and self._picked not in self._placed:
            return False
        return True

    def summary(self) -> dict[str, Any]:
        return {
            "picked": self._picked,
            "placed": sorted(self._placed),
            "failed": sorted(self._failed),
            "attempts": dict(self._attempts),
        }
