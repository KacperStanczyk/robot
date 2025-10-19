"""Robot Framework keywords handling stateful operations such as preconditions."""
from __future__ import annotations

from typing import List

from robot.api.deco import keyword

from ..services.precondition_service import PreconditionService


class StateKeywords:
    """Expose precondition operations to Robot Framework."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, service: PreconditionService):
        self._service = service

    @keyword("PRECOND.Apply")
    def apply_precondition(self, name: str) -> None:
        """Apply the named precondition from the catalog."""

        self._service.apply(name)

    def get_keyword_names(self) -> List[str]:  # pragma: no cover - Robot hook
        return ["PRECOND.Apply"]


__all__ = ["StateKeywords"]
