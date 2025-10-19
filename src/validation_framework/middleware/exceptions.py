"""Exceptions reflecting domain level failure semantics."""


class MiddlewareError(RuntimeError):
    """Base class for middleware level failures."""


class EnvironmentFault(MiddlewareError):
    """Raised when the test environment behaves unexpectedly."""


class SutFault(MiddlewareError):
    """Raised when the system under test fails to respond as required."""


__all__ = ["MiddlewareError", "EnvironmentFault", "SutFault"]
