"""Factory and lifecycle manager for HAL port instances."""
from __future__ import annotations

import logging
from typing import Dict

from ..exceptions import CanError
from ..ports.base_can_port import BaseCanPort
from .hil_can_port import HilCanPort
from .mock_can_port import MockCanPort


class HalManager:
    """Provide access to CAN ports across execution modes."""

    def __init__(self, mode: str, config: Dict[str, Dict], logger: logging.Logger):
        self._mode = mode.upper()
        self._config = config
        self._logger = logger
        self._can_ports: Dict[str, BaseCanPort] = {}

    def get_can_port(self, bus_name: str) -> BaseCanPort:
        if bus_name in self._can_ports:
            return self._can_ports[bus_name]

        port_config = self._config.get("interfaces", {}).get("can", {}).get(bus_name, {})
        self._logger.debug("Creating CAN port for %s in %s mode", bus_name, self._mode)

        if self._mode == "HIL":
            port = HilCanPort(bus_name, self._logger, **port_config)
        elif self._mode in {"MOCK", "SIL"}:
            port = MockCanPort(bus_name, self._logger)
        else:
            raise CanError(f"Unsupported execution mode: {self._mode}")

        self._can_ports[bus_name] = port
        return port


__all__ = ["HalManager"]
