"""In-memory CAN port suitable for MOCK and SIL execution modes."""
from __future__ import annotations

import collections
import logging
import time
from typing import Deque

from ..exceptions import CanTimeoutError
from ..ports.base_can_port import BaseCanPort
from ..types.can_types import CanMessage, TransmissionResult


class MockCanPort(BaseCanPort):
    """Thread-safe CAN port that stores messages in memory."""

    def __init__(self, bus_name: str, logger: logging.Logger):
        super().__init__(bus_name, logger)
        self._rx_queue: Deque[CanMessage] = collections.deque()

    def inject_message(self, message: CanMessage) -> None:
        """Inject a message as if it was received from the bus."""

        self._rx_queue.append(message.with_timestamp())

    def send(self, message: CanMessage) -> TransmissionResult:
        self.logger.debug("[%s] MOCK SEND %s", self.bus_name, message)
        # In mock mode we simply acknowledge the message.
        return TransmissionResult(success=True, timestamp=time.time())

    def receive(self, timeout_s: float = 1.0) -> CanMessage:
        if not self._rx_queue:
            self.logger.debug("[%s] MOCK RECEIVE waiting for message", self.bus_name)
        start = time.time()
        while time.time() - start < timeout_s:
            if self._rx_queue:
                message = self._rx_queue.popleft()
                self.logger.debug("[%s] MOCK RECEIVE %s", self.bus_name, message)
                return message
            time.sleep(0.01)
        raise CanTimeoutError(f"Timeout on bus {self.bus_name} after {timeout_s}s")


__all__ = ["MockCanPort"]
