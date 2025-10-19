"""Middleware orchestrating signal interactions across the HAL."""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from ..config_loader.models import SignalCatalog, SignalDefinition
from ..hal.exceptions import CanTimeoutError, HalError
from ..hal.implementations.hal_manager import HalManager
from ..hal.types.can_types import CanMessage
from .exceptions import EnvironmentFault, SutFault


class InteractionBroker:
    """Translate domain level interactions into HAL calls."""

    def __init__(self, config: SignalCatalog, hal_manager: HalManager, logger: logging.Logger):
        self._config = config
        self._hal = hal_manager
        self._logger = logger

    def set_signal(self, signal_name: str, value: Any) -> None:
        signal_def = self._config.get(signal_name)
        can_port = self._hal.get_can_port(signal_def.bus)
        message = self._encode(signal_def, value)
        try:
            result = can_port.send(message)
        except HalError as exc:
            raise EnvironmentFault(f"HAL failure while sending {signal_name}: {exc}") from exc

        if not result.success:
            raise EnvironmentFault(
                f"Transmission on bus {signal_def.bus} failed: {result.error_message}"
            )

    def wait_for_signal(
        self,
        signal_name: str,
        expected_value: Any,
        timeout_s: Optional[float] = None,
        polling_interval: float = 0.1,
    ) -> None:
        signal_def = self._config.get(signal_name)
        can_port = self._hal.get_can_port(signal_def.bus)
        deadline = None if timeout_s is None else time.time() + timeout_s

        while True:
            if deadline and time.time() > deadline:
                raise SutFault(
                    f"System did not produce signal {signal_name}={expected_value} before timeout"
                )
            try:
                message = can_port.receive(timeout_s=polling_interval)
            except CanTimeoutError:
                if deadline is None:
                    continue
                if time.time() > deadline:
                    raise SutFault(
                        f"Timeout waiting for {signal_name}={expected_value} on bus {signal_def.bus}"
                    )
                continue
            except HalError as exc:
                raise EnvironmentFault(f"HAL failure while waiting for {signal_name}: {exc}") from exc

            decoded = self._decode(signal_def, message)
            if decoded == expected_value:
                self._logger.debug("%s satisfied with value %s", signal_name, decoded)
                return

    def _encode(self, signal_def: SignalDefinition, value: Any) -> CanMessage:
        if signal_def.payload.type == "enum":
            try:
                payload_value = signal_def.payload.mapping[str(value).upper()]
            except KeyError as exc:
                raise ValueError(
                    f"Value {value!r} is not valid for signal {signal_def.name}"
                ) from exc
        else:
            payload_value = int(value)

        data = payload_value.to_bytes(1, byteorder="big")
        return CanMessage(can_id=signal_def.can_id, data=data)

    def _decode(self, signal_def: SignalDefinition, message: CanMessage) -> Any:
        payload = int.from_bytes(message.data[:1], byteorder="big")
        if signal_def.payload.type == "enum":
            for key, value in signal_def.payload.mapping.items():
                if value == payload:
                    return key
            return payload
        return payload


__all__ = ["InteractionBroker"]
