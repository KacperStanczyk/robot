"""Robot Framework keywords exposing HMI functionality."""
from __future__ import annotations

from typing import List

from robot.api.deco import keyword

from ..services.hmi_service import HmiService


class HmiKeywords:
    """Keywords wrapping :class:`HmiService`."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self, service: HmiService):
        self._service = service

    @keyword("HMI.Press")
    def press(self, control: str) -> None:
        """Simulate a physical press on an HMI control."""

        self._service.press(control)

    @keyword("HMI.Navigate")
    def navigate(self, path: str) -> None:
        """Navigate through an HMI path such as ``Settings->Lights``."""

        self._service.navigate(path)

    @keyword("HMI.Expect Telltale")
    def expect_telltale(self, name: str, state: str) -> None:
        """Assert that the cluster telltale ``name`` is in ``state``."""

        self._service.expect_telltale(name, state)

    @keyword("HMI.Open App")
    def open_app(self, app: str) -> None:
        """Launch an IVI application by name."""

        self._service.open_app(app)

    @keyword("HMI.Select")
    def select(self, option_path: str) -> None:
        """Select an option within the current HMI context."""

        self._service.select(option_path)

    @keyword("WIPERS.Activate Mode")
    def activate_wipers(self, mode: str) -> None:
        """Backward compatible keyword to activate wipers in ``mode``."""

        self._service.activate_wipers(mode)

    @keyword("BUS.Set Signal")
    def set_signal(self, signal: str, value) -> None:
        """Forward a raw signal update to the domain layer."""

        self._service.set_signal(signal, value)

    @keyword("BUS.Wait For Signal ==")
    def wait_for_signal(self, signal: str, value, timeout: float = 5.0) -> None:
        """Wait until ``signal`` equals ``value`` within ``timeout`` seconds."""

        self._service.wait_for_signal(signal, value, float(timeout))

    def get_keyword_names(self) -> List[str]:  # pragma: no cover - Robot hook
        return [
            "HMI.Press",
            "HMI.Navigate",
            "HMI.Expect Telltale",
            "HMI.Open App",
            "HMI.Select",
            "WIPERS.Activate Mode",
            "BUS.Set Signal",
            "BUS.Wait For Signal ==",
        ]


__all__ = ["HmiKeywords"]
