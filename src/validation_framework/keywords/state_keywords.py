"""Robot Framework keywords handling stateful operations such as preconditions."""
from __future__ import annotations

from typing import List

from ..services.precondition_service import PreconditionService


class StateKeywords:
    """Expose precondition operations to Robot Framework."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, service: PreconditionService):
        self._service = service

    def set_vehicle_state(self, name: str) -> None:
        """Apply the named precondition."""

        self._service.apply(name)

    def get_keyword_names(self) -> List[str]:  # pragma: no cover - Robot hook
        return ["Set Vehicle State"]


__all__ = ["StateKeywords"]
