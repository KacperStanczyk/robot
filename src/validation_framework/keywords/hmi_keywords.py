"""Robot Framework keywords exposing HMI functionality."""
from __future__ import annotations

from typing import List

from ..services.hmi_service import HmiService


class HmiKeywords:
    """Keywords wrapping :class:`HmiService`."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, service: HmiService):
        self._service = service

    def activate_wipers(self, mode: str) -> None:
        """Activate the wipers in the given ``mode``."""

        self._service.activate_wipers(mode)

    def set_signal(self, signal: str, value) -> None:
        """Forward a raw signal update to the service."""

        self._service.set_signal(signal, value)

    def get_keyword_names(self) -> List[str]:  # pragma: no cover - Robot hook
        return ["Activate Wipers", "Set Signal"]


__all__ = ["HmiKeywords"]
