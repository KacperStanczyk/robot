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
        self._actions: Dict[str, Callable[[str], None]] = {
            "set_signal": self._set_signal,
            "wait_for_signal": self._wait_for_signal,
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

    def _dispatch(self, action: str, target: str, value) -> None:
        if action not in self._actions:
            raise KeyError(f"Unsupported precondition action: {action}")
        self._actions[action](target, value)

    def _set_signal(self, target: str, value) -> None:
        self._broker.set_signal(target, value)

    def _wait_for_signal(self, target: str, value) -> None:
        self._broker.wait_for_signal(target, value, timeout_s=5)

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
