"""Hardware backed CAN port intended for use on HIL benches."""
from __future__ import annotations

import logging
from typing import Any, Dict

from ..exceptions import CanError, CanTimeoutError
from ..ports.base_can_port import BaseCanPort
from ..types.can_types import CanMessage, TransmissionResult


class HilCanPort(BaseCanPort):
    """Adapter around python-can providing the HAL contract."""

    def __init__(self, bus_name: str, logger: logging.Logger, **can_config: Dict[str, Any]):
        super().__init__(bus_name, logger)
        try:
            import can  # type: ignore
        except ImportError as exc:  # pragma: no cover - executed only without dependency
            raise CanError(
                "python-can must be installed to use HilCanPort"
            ) from exc

        try:
            self._bus = can.interface.Bus(channel=can_config.get("channel", bus_name), **can_config)
        except Exception as exc:  # pragma: no cover - depends on hardware
            raise CanError(f"Failed to initialise CAN bus {bus_name}: {exc}") from exc

        self._can = can

    def send(self, message: CanMessage) -> TransmissionResult:
        payload = self._can.Message(
            arbitration_id=message.can_id,
            data=message.data,
            is_extended_id=message.is_extended_id,
        )
        try:
            self._bus.send(payload)
            self.logger.debug("[%s] HIL SEND %s", self.bus_name, message)
            return TransmissionResult(success=True)
        except self._can.CanError as exc:  # pragma: no cover - hardware failure path
            self.logger.error("[%s] HIL SEND failed: %s", self.bus_name, exc)
            return TransmissionResult(success=False, error_message=str(exc))

    def receive(self, timeout_s: float = 1.0) -> CanMessage:
        payload = self._bus.recv(timeout=timeout_s)
        if payload is None:
            raise CanTimeoutError(f"Timeout on bus {self.bus_name} after {timeout_s}s")
        return CanMessage(
            can_id=payload.arbitration_id,
            data=bytes(payload.data),
            is_extended_id=payload.is_extended_id,
            timestamp=payload.timestamp,
        )


__all__ = ["HilCanPort"]
