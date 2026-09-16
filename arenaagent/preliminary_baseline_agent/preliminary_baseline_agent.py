from __future__ import annotations

import os
import json
from typing import Any

from loguru import logger

from arenaagent.builder import Register
from arenaagent.utils.configclass import configclass
from arenaagent.vlm_agent.vlm_agent import VLMAgent, VLMAgentCfg

from .strategies import (
    TidyRoomGuard,
    build_strategy,
    object_size,
    subject_identity,
    task_type_of,
)


# Only the actions that can actually move each task forward are sent to the
# model. Unknown task types keep the full action space.
_TASK_ACTION_ALLOWLIST: dict[str, set[str]] = {
    "counting": {
        "turn_in_degree",
        "move_to_location",
        "move_to_object",
        "submit_answer",
        "finish_task",
    },
    "raven": {
        "solve_raven",
        "submit_answer",
        "finish_task",
    },
    "jigsaw": {
        "look_at_location",
        "look_at_object",
        "move_to_location",
        "move_to_object",
        "move_forward",
        "move_backward",
        "turn_in_degree",
        "move_and_take_object",
        "put_down_sth",
        "move_and_put_down",
        "submit_puzzle_answer",
        "finish_task",
    },
    "tidyroom": {
        "look_at_location",
        "look_at_object",
        "move_to_location",
        "move_to_object",
        "move_forward",
        "move_backward",
        "turn_in_degree",
        "move_and_take_object",
        "put_down_sth",
        "move_and_put_down",
        "move_and_put_down_object_in_container",
        "finish_task",
    },
}

_COMPACT_HISTORY_LIMIT = 5


@configclass
class PreliminaryBaselineAgentCfg(VLMAgentCfg):
    name: str = "preliminary_baseline_agent"


@Register("preliminary_baseline_agent")
class PreliminaryBaselineAgent(VLMAgent):
    def __init__(
        self,
        stub,
        channel,
        cfg: PreliminaryBaselineAgentCfg | None = None,
        sleep_between_steps: float = 2.0,
    ) -> None:
        super().__init__(
            stub=stub,
            channel=channel,
            cfg=cfg or PreliminaryBaselineAgentCfg(),
            sleep_between_steps=sleep_between_steps,
        )
        self._active_task_key: str = ""
        self._active_task_type: str = ""
        self._task_strategy: Any = None
        self._tidy_guard = TidyRoomGuard()

    def _task_key(self, subject: Any) -> str:
        return subject_identity(subject)

    def _reset_task_state(self, subject: Any) -> None:
        """Reset per-subject state and route the subject to a strategy."""

        self._active_task_key = self._task_key(subject)
        self._active_task_type = task_type_of(subject)
        self.history_messages = []
        self.last_json_parse_message = {}
        self._action_histories = []
        self._last_action_res = {}
        self._last_apply_resp = {}
        self._handled_piece_transfers = set()
        self._raven_candidates_cache = {}
        self._raven_next_index = {}
        self._tidy_guard.begin(subject)

        strategy = build_strategy(self._active_task_type, self)
        if strategy is not None and not strategy.can_handle(subject):
            strategy = None
        self._task_strategy = strategy
        logger.info(
            "Task route: type={} strategy={}",
            self._active_task_type,
            getattr(strategy, "name", "vlm"),
        )

    def _execute_strategy_action(self, strategy: Any, action: dict[str, Any]) -> dict[str, Any]:
        result = self._do_action(action)
        self._last_action_res = result if isinstance(result, dict) else {}
        self._action_histories.append(
            {
                "action": action,
                "result": self._last_action_res,
                "strategy": getattr(strategy, "name", ""),
            }
        )
        self._trim_action_histories()
        logger.info(
            "Strategy {} action={} result={}",
            getattr(strategy, "name", ""),
            action.get("action"),
            self._last_action_res,
        )
        return self._last_action_res

    def _run_strategy(self, subject: Any, task_response: dict[str, Any]) -> dict[str, Any] | None:
        strategy = self._task_strategy
        if strategy is None:
            return None
        try:
            outcome = strategy.step(subject, task_response)
        except Exception as exc:
            logger.exception("Strategy {} failed, falling back to VLM: {}", getattr(strategy, "name", ""), exc)
            self._task_strategy = None
            return None
        if outcome is None:
            return None
        logger.info(
            "Strategy {} outcome: action={} payload={} finish={} note={}",
            getattr(strategy, "name", ""),
            bool(outcome.action),
            bool(outcome.payload),
            outcome.finish,
            outcome.note,
        )
        if outcome.action is not None:
            return self._execute_strategy_action(strategy, outcome.action)
        if outcome.payload is not None:
            self._last_action_res = outcome.payload
            return outcome.payload
        if outcome.finish:
            return self._execute_strategy_action(
                strategy,
                {
                    "action": "finish_task",
                    "output": 0,
                    "think": outcome.note or "strategy finished",
                },
            )
        return None

    def run_step(self, subject: Any, task_response: dict[str, Any]) -> dict[str, Any]:
        key = self._task_key(subject)
        if key != self._active_task_key:
            self._reset_task_state(subject)
        result = self._run_strategy(subject, task_response)
        if result is not None:
            return result
        return super().run_step(subject, task_response)

    def _tidy_task_active(self) -> bool:
        return self._active_task_type == "tidyroom"

    def _handle_move_and_take(self, params: dict[str, Any], action: dict[str, Any]) -> Any:
        object_id = self._get_param(params, "object_id", "object")
        if self._tidy_task_active() and not self._tidy_guard.can_attempt(object_id):
            logger.warning("TidyRoomGuard blocked repeated take of {}", object_id)
            return self._fail_result(error="object failed too many times; choose another target")
        result = super()._handle_move_and_take(params, action)
        if self._tidy_task_active():
            self._tidy_guard.record_take(object_id, result)
        return result

    def _handle_put_down_sth(self, params: dict[str, Any], action: dict[str, Any]) -> Any:
        result = super()._handle_put_down_sth(params, action)
        if self._tidy_task_active():
            self._tidy_guard.record_place(None, result)
        return result

    def _handle_finish(self, params: dict[str, Any], action: dict[str, Any]) -> Any:
        in_hand = False
        try:
            if self.tongsim is not None and self.character_id is not None:
                in_hand, _ = self.tongsim.has_object_in_hand(self.character_id)
        except Exception as exc:
            logger.warning("finish guard could not read hand state: {}", exc)
        if self._tidy_task_active() and not self._tidy_guard.can_finish(in_hand):
            logger.warning("TidyRoomGuard blocked finish_task (in_hand={})", in_hand)
            return self._fail_result(error="cannot finish tidy-room while still holding an item")
        return super()._handle_finish(params, action)


    def _should_handle_piece_transfer(self) -> bool:
        return False


    def _filter_api_info(self, task_type: str, api_info: Any) -> Any:
        """Expose only the actions that can help the current task."""

        allowlist = _TASK_ACTION_ALLOWLIST.get(str(task_type or "").strip().lower())
        if not allowlist or not isinstance(api_info, dict):
            return api_info
        filtered = {name: info for name, info in api_info.items() if name in allowlist}
        if not filtered:
            return api_info
        logger.debug(
            "Task {}: filtered api_info from {} to {} actions",
            task_type,
            len(api_info),
            len(filtered),
        )
        return filtered

    @staticmethod
    def _filter_visible_objects(task_type: str, objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Drop zero-size perception markers before sending objects to the model."""

        if str(task_type or "").strip().lower() != "counting" or not objects:
            return objects
        real_objects = [
            obj
            for obj in objects
            if isinstance(obj, dict) and max(object_size(obj)) > 0.01
        ]
        return real_objects or objects

    def _compact_action_histories(self, task_type: str) -> list[dict[str, Any]]:
        """Send a compact action summary instead of raw histories for the four tasks."""

        if str(task_type or "").strip().lower() not in _TASK_ACTION_ALLOWLIST:
            return self._action_histories

        compact: list[dict[str, Any]] = []
        for entry in self._action_histories[-_COMPACT_HISTORY_LIMIT:]:
            if not isinstance(entry, dict):
                continue
            action = entry.get("action") if isinstance(entry.get("action"), dict) else {}
            result = entry.get("result") if isinstance(entry.get("result"), dict) else {}
            item: dict[str, Any] = {"action": action.get("action")}
            params = action.get("parameters")
            if isinstance(params, dict) and params:
                item["params"] = params
            if result.get("result"):
                item["result"] = result.get("result")
            if result.get("error"):
                item["error"] = result["error"]
            compact.append(item)
        return compact


    def _load_task_spec_prompts(self) -> dict[str, str]:
        if self._task_spec_prompt_cache is not None:
            return self._task_spec_prompt_cache

        try:
            here = os.path.dirname(os.path.abspath(__file__))
            task_spec_prompt_path = os.path.join(here, "prompts", "task_spec_prompt.json")
            with open(task_spec_prompt_path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                self._task_spec_prompt_cache = {str(key): str(value) for key, value in loaded.items()}
            else:
                self._task_spec_prompt_cache = {}
        except Exception as exc:
            logger.warning(f"加载 task_spec_prompt.json 失败: {exc}")
            self._task_spec_prompt_cache = {}

        return self._task_spec_prompt_cache

    def _build_prompt_variables(
        self,
        subject: Any,
        task_response: dict[str, Any],
        api_info: Any,
        visible_objects_info: list[dict[str, Any]],
        object_in_hand: Any,
    ) -> dict[str, Any]:
        task_type = subject.get("task_type", "") if isinstance(subject, dict) else ""
        task_prompt = self._load_task_spec_prompts().get(task_type, "") if task_type else ""
        api_info = self._filter_api_info(task_type, api_info)
        visible_objects_info = self._filter_visible_objects(task_type, visible_objects_info)

        if task_type == "jigsaw" and isinstance(subject, dict):
            reference_bounding = subject.get("reference_bounding", [])
            if reference_bounding and len(reference_bounding) >= 4:
                bounding_str = (
                    f"[Y: {reference_bounding[0]:.1f} ~ {reference_bounding[2]:.1f}, "
                    f"Z: {reference_bounding[3]:.1f} ~ {reference_bounding[1]:.1f}]"
                )
                task_prompt = (
                    f"{task_prompt}\n你需要将拼图块放置到{bounding_str}区域内。"
                    if task_prompt
                    else f"你需要将拼图块放置到{bounding_str}区域内。"
                )

        if task_type == "tidyroom":
            candidates = self._tidy_guard.filter_objects(visible_objects_info)
            candidate_ids = [
                str(obj.get("object_id"))
                for obj in candidates
                if obj.get("object_id") is not None
            ]
            guard = self._tidy_guard.summary()
            guard_lines = [
                "",
                "【整理状态约束】",
                f"优先抓取这些可见物体ID：{candidate_ids}",
                f"这些ID已多次抓取失败，禁止再次尝试：{guard.get('failed', [])}",
                f"已完成放置：{guard.get('placed', [])}",
                "手中持有物品时禁止调用 finish_task，必须先放到合适位置。",
                "同一物体最多尝试两次，失败后立即换下一个目标。",
            ]
            guard_text = "\n".join(guard_lines)
            task_prompt = f"{task_prompt}\n{guard_text}" if task_prompt else guard_text

        logger.debug("_last_action_res {}", self._last_action_res)

        return {
            "api_info": api_info,
            "example_objects_info": visible_objects_info[0] if len(visible_objects_info) > 0 else {},
            "task_text": subject["subject"],
            "task_prompt": task_prompt,
            "visiable_objects_info": visible_objects_info,
            "object_in_hand": object_in_hand,
            "response": task_response,
            "npc_reply": self._last_npc_reply,
            "npc_subject": self._last_npc_subject or {},
            "action_res": self._serialize_prompt_status(self._last_action_res),
            "apply_resp": self._serialize_prompt_status(self._last_apply_resp),
            "action_histories": self._compact_action_histories(task_type),
        }
