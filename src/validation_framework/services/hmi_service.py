"""Domain oriented service for Human Machine Interface operations."""
from __future__ import annotations

from typing import Any

from .domain_service import DomainService


class HmiService:
    """Encapsulates HMI logic using the InteractionBroker."""

    def __init__(self, domain: DomainService):
        self._domain = domain

    def activate_wipers(self, mode: str) -> None:
        """Activate the wipers in a particular mode."""

        self._domain.set_wiper_mode(mode)
        self._domain.verify_wipers_state("ACTIVE")

    def set_signal(self, signal: str, value: Any) -> None:
        self._domain.set_signal(signal, value)

    def wait_for_signal(self, signal: str, value: Any, timeout_s: float) -> None:
        self._domain.wait_for_signal(signal, value, timeout_s=timeout_s)

    def press(self, control: str) -> None:
        self._domain.hmi_press(control)

    def navigate(self, path: str) -> None:
        self._domain.hmi_navigate(path)

    def expect_telltale(self, name: str, state: str) -> None:
        self._domain.expect_telltale(name, state)

    def open_app(self, app: str) -> None:
        self._domain.hmi_open_app(app)

    def select(self, option_path: str) -> None:
        self._domain.hmi_select(option_path)


__all__ = ["HmiService"]
