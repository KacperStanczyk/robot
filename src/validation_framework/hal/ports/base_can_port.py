"""Abstract contract for CAN ports."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from ..exceptions import CanTimeoutError
from ..types.can_types import CanMessage, TransmissionResult


class BaseCanPort(ABC):
    """Bidirectional interface for communicating with a CAN bus."""

    def __init__(self, bus_name: str, logger: logging.Logger):
        self.bus_name = bus_name
        self.logger = logger

    @abstractmethod
    def send(self, message: CanMessage) -> TransmissionResult:
        """Send a message on the bus."""

    @abstractmethod
    def receive(self, timeout_s: float = 1.0) -> CanMessage:
        """Receive the next message from the bus.

        Implementations MUST raise :class:`CanTimeoutError` when no message is
        available before ``timeout_s`` expires.
        """


__all__ = ["BaseCanPort"]
