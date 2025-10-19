"""Domain specific exceptions for the hardware abstraction layer."""


class HalError(RuntimeError):
    """Base class for HAL related failures."""


class CanError(HalError):
    """Raised when a CAN interface encounters a non-recoverable error."""


class CanTimeoutError(HalError):
    """Raised when no CAN message is received within the allocated time."""


__all__ = ["HalError", "CanError", "CanTimeoutError"]
