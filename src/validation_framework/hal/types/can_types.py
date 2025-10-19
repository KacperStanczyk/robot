"""Domain specific types used by CAN ports."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import NamedTuple, Optional


@dataclass
class CanMessage:
    """Representation of a CAN frame."""

    can_id: int
    data: bytes
    is_extended_id: bool = False
    timestamp: Optional[float] = None

    def with_timestamp(self) -> "CanMessage":
        """Return a copy of the message with a capture timestamp."""

        return CanMessage(
            can_id=self.can_id,
            data=self.data,
            is_extended_id=self.is_extended_id,
            timestamp=time.time() if self.timestamp is None else self.timestamp,
        )


class TransmissionResult(NamedTuple):
    """Outcome of attempting to send a CAN frame."""

    success: bool
    error_message: Optional[str] = None
    timestamp: float = time.time()


__all__ = ["CanMessage", "TransmissionResult"]
