"""Domain oriented service for Human Machine Interface operations."""
from __future__ import annotations

from typing import Any

from ..middleware.broker import InteractionBroker


class HmiService:
    """Encapsulates HMI logic using the InteractionBroker."""

    def __init__(self, broker: InteractionBroker):
        self._broker = broker

    def activate_wipers(self, mode: str) -> None:
        """Activate the wipers in a particular mode."""

        self._broker.set_signal("WiperRequest", mode)
        self._broker.wait_for_signal("WiperMotorStatus", "ACTIVE", timeout_s=5)

    def set_signal(self, signal: str, value: Any) -> None:
        self._broker.set_signal(signal, value)

    def wait_for_signal(self, signal: str, value: Any, timeout_s: float) -> None:
        self._broker.wait_for_signal(signal, value, timeout_s=timeout_s)


__all__ = ["HmiService"]
