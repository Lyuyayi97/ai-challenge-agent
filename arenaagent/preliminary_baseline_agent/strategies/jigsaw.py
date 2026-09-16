from __future__ import annotations

from typing import Any

from loguru import logger

from .base import StrategyOutcome, TaskStrategy, task_type_of


class JigsawStrategy(TaskStrategy):
    """Deterministic path for jigsaw stages that expose piece targets.

    When the subject provides ``piece_object_id``, ``piece_loc``,
    ``place_piece_target_loc`` and ``place_piece_target_rot`` the existing
    specialised transfer routine is used directly instead of asking the VLM
    to plan navigation. Stages without those fields keep the VLM path, which
    now receives the corrected Y-Z grid prompt.
    """

    name = "jigsaw"
    MAX_ATTEMPTS_PER_PIECE = 3
    _REQUIRED_FIELDS = (
        "piece_object_id",
        "piece_loc",
        "place_piece_target_loc",
        "place_piece_target_rot",
    )

    def __init__(self, agent: Any) -> None:
        super().__init__(agent)
        self._attempts: dict[str, int] = {}
        self._disabled = False

    def can_handle(self, subject: Any) -> bool:
        return task_type_of(subject) == "jigsaw"

    def reset(self, subject: Any) -> None:
        self._attempts = {}
        self._disabled = False

    def step(
        self,
        subject: Any,
        task_response: dict[str, Any] | None = None,
    ) -> StrategyOutcome | None:
        if self._disabled or not isinstance(subject, dict):
            return None

        missing = [key for key in self._REQUIRED_FIELDS if subject.get(key) is None]
        if missing:
            logger.debug("JigsawStrategy: deterministic payload missing {}, using VLM path", missing)
            return None

        piece_id = str(subject.get("piece_object_id"))
        attempts = self._attempts.get(piece_id, 0)
        if attempts >= self.MAX_ATTEMPTS_PER_PIECE:
            logger.warning("JigsawStrategy: piece {} exceeded attempts, disabling strategy", piece_id)
            self._disabled = True
            return None
        self._attempts[piece_id] = attempts + 1

        transfer = getattr(self.agent, "_maybe_handle_piece_transfer", None)
        if not callable(transfer):
            return None
        result = transfer(subject)
        if isinstance(result, dict) and result.get("piece_transfer_done"):
            logger.info("JigsawStrategy placed piece {} (attempt {})", piece_id, attempts + 1)
            return StrategyOutcome.from_payload(result, note=f"piece {piece_id}")
        return None

    def summary(self) -> dict[str, Any]:
        return {"attempts": dict(self._attempts), "disabled": self._disabled}
