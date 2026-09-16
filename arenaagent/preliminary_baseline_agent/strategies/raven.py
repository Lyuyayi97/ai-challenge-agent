from __future__ import annotations

import os
from typing import Any

from loguru import logger

from .base import StrategyOutcome, TaskStrategy, task_type_of


class RavenStrategy(TaskStrategy):
    """Direct path for the Raven task.

    The Raven solver is deterministic and local. The generic VLM loop is
    bypassed so the first answer is submitted immediately; when an answer is
    rejected the next ranked candidate is submitted without any movement.
    """

    name = "raven"
    MAX_SUBMISSIONS = 8

    def __init__(self, agent: Any) -> None:
        super().__init__(agent)
        self._submitted: set[str] = set()
        self._fallback = False

    def can_handle(self, subject: Any) -> bool:
        return task_type_of(subject) == "raven"

    def reset(self, subject: Any) -> None:
        self._submitted = set()
        self._fallback = False

    def _ensure_images(self, subject: Any) -> bool:
        current = str(getattr(self.agent, "_raven_image_temp_path", "") or "")
        if current and os.path.exists(current):
            return True
        if not isinstance(subject, dict):
            return False
        for key in ("task_data", "stage_data"):
            data = subject.get(key)
            if not data:
                continue
            try:
                self.agent._materialize_task_data_images(data)
            except Exception as exc:
                logger.warning("Raven image materialization failed: {}", exc)
                continue
            current = str(getattr(self.agent, "_raven_image_temp_path", "") or "")
            if current and os.path.exists(current):
                return True
        return False

    @staticmethod
    def _extract_answer(result: dict[str, Any]) -> Any:
        for key, value in result.items():
            if key in {"result", "error"}:
                continue
            if value is not None:
                return value
        return None

    def step(
        self,
        subject: Any,
        task_response: dict[str, Any] | None = None,
    ) -> StrategyOutcome | None:
        if self._fallback:
            return None
        if not self._ensure_images(subject):
            logger.warning("RavenStrategy: no usable task image, falling back to VLM")
            self._fallback = True
            return None

        from arenaagent.vlm_agent.raven_skill import handle as handle_raven_skill

        result = handle_raven_skill(self.agent, {}, {"action": "solve_raven"})
        if not isinstance(result, dict) or result.get("result") == "failed" or result.get("error"):
            logger.warning("RavenStrategy: solver failed, falling back to VLM: {}", result)
            self._fallback = True
            return None

        answer = self._extract_answer(result)
        if answer is None:
            self._fallback = True
            return None

        answer_key = str(answer)
        if answer_key in self._submitted or len(self._submitted) >= self.MAX_SUBMISSIONS:
            logger.info("RavenStrategy: candidates exhausted, finishing")
            return StrategyOutcome.finished(note="raven candidates exhausted")
        self._submitted.add(answer_key)
        logger.info("RavenStrategy submit candidate {} (attempt {})", answer, len(self._submitted))
        return StrategyOutcome.from_payload(result, note=f"raven answer {answer}")

    def summary(self) -> dict[str, Any]:
        return {"submitted": sorted(self._submitted), "fallback": self._fallback}
