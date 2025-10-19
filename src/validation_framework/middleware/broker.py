"""Middleware orchestrating signal interactions across the HAL."""
from __future__ import annotations

import logging
import time
from typing import Any, Iterable, Optional

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

            if message.can_id != signal_def.can_id:
                self._logger.debug(
                    "Ignoring CAN id %s while waiting for %s", message.can_id, signal_def.name
                )
                continue

            decoded = self._decode(signal_def, message)
            if decoded == expected_value:
                self._logger.debug("%s satisfied with value %s", signal_name, decoded)
                return

    def get_signal(self, signal_name: str, timeout_s: float = 1.0) -> Any:
        """Retrieve the latest value for ``signal_name`` within ``timeout_s`` seconds."""

        signal_def = self._config.get(signal_name)
        can_port = self._hal.get_can_port(signal_def.bus)
        deadline = time.time() + timeout_s

        while True:
            remaining = max(deadline - time.time(), 0.0)
            if remaining <= 0.0:
                raise SutFault(f"Did not observe signal {signal_name} before timeout")
            try:
                message = can_port.receive(timeout_s=min(remaining, 0.1))
            except CanTimeoutError:
                continue
            except HalError as exc:
                raise EnvironmentFault(f"HAL failure while reading {signal_name}: {exc}") from exc

            if message.can_id != signal_def.can_id:
                self._logger.debug(
                    "Ignoring CAN id %s while reading %s", message.can_id, signal_def.name
                )
                continue

            value = self._decode(signal_def, message)
            self._logger.debug("Read %s=%s", signal_name, value)
            return value

    def assert_signal_equal(self, signal_name: str, expected_value: Any, timeout_s: float = 1.0) -> None:
        """Assert that ``signal_name`` eventually equals ``expected_value``."""

        observed = self.get_signal(signal_name, timeout_s=timeout_s)
        if observed != expected_value:
            raise SutFault(
                f"Signal {signal_name} expected {expected_value!r} but observed {observed!r}"
            )

    def assert_signal_in(
        self, signal_name: str, expected_values: Iterable[Any], timeout_s: float = 1.0
    ) -> None:
        """Ensure that ``signal_name`` resolves to one of ``expected_values``."""

        observed = self.get_signal(signal_name, timeout_s=timeout_s)
        if observed not in expected_values:
            formatted = ", ".join(repr(value) for value in expected_values)
            raise SutFault(
                f"Signal {signal_name} expected to be in {{{formatted}}} but was {observed!r}"
            )

    def assert_signal_in_range(
        self,
        signal_name: str,
        minimum: float,
        maximum: float,
        timeout_s: float = 1.0,
    ) -> None:
        """Check that ``signal_name`` lies within ``minimum`` and ``maximum`` inclusive."""

        observed = self.get_signal(signal_name, timeout_s=timeout_s)
        if not (minimum <= float(observed) <= maximum):
            raise SutFault(
                f"Signal {signal_name} expected between {minimum} and {maximum} but was {observed!r}"
            )

    def assert_consistent_signals(
        self, signal_names: Iterable[str], timeout_s: float = 1.0
    ) -> None:
        """Validate that all signals in ``signal_names`` converge to the same value."""

        observed_values = {
            name: self.get_signal(name, timeout_s=timeout_s) for name in signal_names
        }
        unique_values = set(observed_values.values())
        if len(unique_values) > 1:
            raise SutFault(
                "Signals are inconsistent: "
                + ", ".join(f"{name}={value!r}" for name, value in observed_values.items())
            )

    def assert_no_faults(self, fault_signal_names: Iterable[str], timeout_s: float = 1.0) -> None:
        """Ensure that all provided fault indicator signals resolve to a healthy state."""

        for name in fault_signal_names:
            observed = self.get_signal(name, timeout_s=timeout_s)
            if observed not in (0, "NONE", "INACTIVE", "OK"):
                raise EnvironmentFault(
                    f"Fault indicator {name} reported unhealthy state {observed!r}"
                )

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
