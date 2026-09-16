from __future__ import annotations

import time
from typing import Any

from loguru import logger

from .base import (
    StrategyOutcome,
    TaskStrategy,
    object_size,
    subject_text,
    task_type_of,
)


# Rules are intentionally conservative: a rule only claims a question when
# the target name maps to visual attributes that the perception payload really
# exposes (color and shape). Objects without a usable AABB are ignored.
_TARGET_RULES: tuple[dict[str, Any], ...] = (
    {
        "terms": ("苹果", "apple"),
        "colors": {"red", "green", "orange", "yellow"},
        "shapes": {"round", "sphere", "circle"},
    },
    {
        "terms": ("橙子", "橘子", "orange"),
        "colors": {"orange"},
        "shapes": {"round", "sphere", "circle"},
    },
    {
        "terms": ("西瓜", "watermelon"),
        "colors": {"green"},
        "shapes": {"round", "sphere", "circle"},
    },
    {
        "terms": ("香蕉", "banana"),
        "colors": {"yellow"},
        "shapes": None,
        "exclude_shapes": {"rectangle", "box"},
    },
    {
        "terms": ("球", "ball"),
        "colors": None,
        "shapes": {"round", "sphere", "circle"},
    },
)


class CountingStrategy(TaskStrategy):
    """Deterministic multi-view counting with an object ledger.

    The VLM is not asked to remember totals. The code turns the character
    through a fixed set of viewpoints, deduplicates objects by object_id, and
    maps the ledger count to the closest not-yet-tried answer option.
    """

    name = "counting"
    MAX_VIEWS = 4
    VIEW_TURN_DEGREE = 90.0
    MAX_SCAN_SECONDS = 180.0
    MAX_SUBMISSIONS = 4

    def __init__(self, agent: Any) -> None:
        super().__init__(agent)
        self._ledger: dict[str, dict[str, Any]] = {}
        self._phase = "scan"
        self._view_index = 0
        self._submitted: set[str] = set()
        self._started_at = 0.0
        self._target_rule: dict[str, Any] | None = None
        self._target_name = ""
        self._options: dict[str, float] = {}

    @staticmethod
    def _match_rule(text: str) -> tuple[dict[str, Any] | None, str]:
        lowered = text.lower()
        for rule in _TARGET_RULES:
            for term in rule["terms"]:
                if term.lower() in lowered:
                    return rule, term
        return None, ""

    def can_handle(self, subject: Any) -> bool:
        if task_type_of(subject) != "counting":
            return False
        text = subject_text(subject)
        if "多少" not in text and "count" not in text.lower():
            return False
        rule, _ = self._match_rule(text)
        return rule is not None

    def reset(self, subject: Any) -> None:
        self._ledger = {}
        self._phase = "scan"
        self._view_index = 0
        self._submitted = set()
        self._started_at = time.monotonic()
        text = subject_text(subject)
        self._target_rule, self._target_name = self._match_rule(text)
        self._options = self._parse_options(subject)
        logger.info(
            "CountingStrategy reset: target={}, options={}",
            self._target_name,
            self._options,
        )

    @staticmethod
    def _parse_options(subject: Any) -> dict[str, float]:
        if not isinstance(subject, dict):
            return {}
        raw = subject.get("options")
        if not isinstance(raw, dict):
            return {}
        parsed: dict[str, float] = {}
        for key, value in raw.items():
            try:
                parsed[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
        return parsed

    def _matches_target(self, obj: dict[str, Any]) -> bool:
        rule = self._target_rule
        if not rule:
            return False
        color = str(obj.get("color") or "").strip().lower()
        shape = str(obj.get("shape") or "").strip().lower()
        colors = rule.get("colors")
        shapes = rule.get("shapes")
        excluded = rule.get("exclude_shapes") or set()
        if colors is not None and color not in colors:
            return False
        if shape in excluded:
            return False
        if shapes is not None and not any(token in shape for token in shapes):
            return False
        return True

    def _update_ledger(self, objects: list[dict[str, Any]]) -> None:
        for obj in objects or []:
            if not isinstance(obj, dict):
                continue
            object_id = str(obj.get("object_id") or "").strip()
            if not object_id:
                continue
            size = object_size(obj)
            if max(size) <= 0.01:
                # Degenerate AABB entries are markers, not physical objects.
                continue
            entry = self._ledger.get(object_id)
            if entry is None:
                entry = {
                    "object_id": object_id,
                    "color": obj.get("color"),
                    "shape": obj.get("shape"),
                    "location": obj.get("place_location"),
                    "world_aabb": obj.get("world_aabb"),
                    "matches_target": self._matches_target(obj),
                    "seen_count": 0,
                }
                self._ledger[object_id] = entry
            entry["seen_count"] = int(entry.get("seen_count") or 0) + 1

    def _matched_ids(self) -> list[str]:
        return [
            object_id
            for object_id, entry in self._ledger.items()
            if entry.get("matches_target")
        ]

    def _turn_action(self) -> dict[str, Any]:
        return {
            "action": "turn_in_degree",
            "parameters": {"degree": self.VIEW_TURN_DEGREE},
            "output": 0,
            "think": f"计数扫描视角 {self._view_index}/{self.MAX_VIEWS}，继续旋转收集视角。",
        }

    def _candidate_values(self, count: int) -> list[float]:
        if self._options:
            return sorted(
                self._options.values(),
                key=lambda value: (abs(value - count), value),
            )
        values = [float(count)]
        for offset in (1, -1, 2, -2):
            candidate = float(max(0, count + offset))
            if candidate not in values:
                values.append(candidate)
        return values

    def _submit_outcome(self) -> StrategyOutcome:
        matched_ids = self._matched_ids()
        count = len(matched_ids)
        for value in self._candidate_values(count):
            answer = str(int(value)) if float(value).is_integer() else str(value)
            if answer in self._submitted:
                continue
            if len(self._submitted) >= self.MAX_SUBMISSIONS:
                break
            self._submitted.add(answer)
            logger.info(
                "CountingStrategy submit answer={} count={} ids={}",
                answer,
                count,
                matched_ids,
            )
            return StrategyOutcome.from_action(
                {
                    "action": "submit_answer",
                    "parameters": {},
                    "output": answer,
                    "think": (
                        f"共观察到 {count} 个目标物体，ID={matched_ids}，"
                        f"提交选项 {answer}。"
                    ),
                },
                note=f"submit {answer}",
            )
        return StrategyOutcome.finished(note="counting candidates exhausted")

    def step(
        self,
        subject: Any,
        task_response: dict[str, Any] | None = None,
    ) -> StrategyOutcome | None:
        if self._target_rule is None:
            self.reset(subject)

        objects = self.agent.capture_observation()
        self._update_ledger(objects)
        self._view_index += 1

        elapsed = time.monotonic() - self._started_at
        if self._phase == "scan" and self._view_index < self.MAX_VIEWS and elapsed < self.MAX_SCAN_SECONDS:
            return StrategyOutcome.from_action(
                self._turn_action(),
                note=f"scan view {self._view_index}",
            )

        self._phase = "submit"
        return self._submit_outcome()

    def summary(self) -> dict[str, Any]:
        return {
            "target": self._target_name,
            "views": self._view_index,
            "ledger_size": len(self._ledger),
            "matched_ids": self._matched_ids(),
            "submitted": sorted(self._submitted),
        }
