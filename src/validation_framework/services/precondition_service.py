"""Service responsible for applying declarative preconditions."""
from __future__ import annotations

import logging
from typing import Callable, Dict

from ..config_loader.models import PreconditionCatalog, PreconditionDefinition
from ..middleware.broker import InteractionBroker
from ..middleware.exceptions import EnvironmentFault


class PreconditionService:
    """Evaluate preconditions using middleware interactions."""

    def __init__(
        self,
        catalog: PreconditionCatalog,
        broker: InteractionBroker,
        logger: logging.Logger,
    ) -> None:
        self._catalog = catalog
        self._broker = broker
        self._logger = logger
        self._actions: Dict[str, Callable[[str, object], None]] = {
            "set_signal": self._set_signal,
            "wait_for_signal": self._wait_for_signal,
            "assert_signal": self._assert_signal,
            "assert_signal_in": self._assert_signal_in,
            "assert_signal_range": self._assert_signal_range,
        }

    def apply(self, name: str) -> None:
        definition = self._catalog.get(name)
        self._logger.info("Applying precondition %s", name)
        try:
            for step in definition.steps:
                self._dispatch(step.action, step.target, step.value)
        except Exception as exc:
            self._logger.error("Precondition %s failed: %s", name, exc)
            self._rollback(definition)
            raise EnvironmentFault(f"Precondition {name} failed: {exc}") from exc

    def register_action(self, name: str, handler: Callable[[str, object], None]) -> None:
        self._actions[name] = handler

    def _dispatch(self, action: str, target: str, value) -> None:
        if action not in self._actions:
            raise KeyError(f"Unsupported precondition action: {action}")
        self._actions[action](target, value)

    def _set_signal(self, target: str, value) -> None:
        self._broker.set_signal(target, value)

    def _wait_for_signal(self, target: str, value) -> None:
        self._broker.wait_for_signal(target, value, timeout_s=5)

    def _assert_signal(self, target: str, value) -> None:
        self._broker.assert_signal_equal(target, value, timeout_s=5)

    def _assert_signal_in(self, target: str, value) -> None:
        expected_values = value if isinstance(value, (list, tuple, set)) else [value]
        self._broker.assert_signal_in(target, expected_values, timeout_s=5)

    def _assert_signal_range(self, target: str, value) -> None:
        if not isinstance(value, dict) or "min" not in value or "max" not in value:
            raise ValueError("assert_signal_range requires a mapping with 'min' and 'max'")
        self._broker.assert_signal_in_range(
            target,
            float(value["min"]),
            float(value["max"]),
            timeout_s=5,
        )

    def _rollback(self, definition: PreconditionDefinition) -> None:
        if not definition.rollback:
            return
        self._logger.info("Rolling back precondition %s", definition.name)
        for step in definition.rollback:
            try:
                self._dispatch(step.action, step.target, step.value)
            except Exception as exc:  # pragma: no cover - failure path
                self._logger.error("Rollback step %s failed: %s", step.action, exc)


__all__ = ["PreconditionService"]
