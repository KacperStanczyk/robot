"""Robot Framework entry point wiring together the validation stack."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from robot.libraries.BuiltIn import BuiltIn

from ..config_loader.models import (
    FrameworkConfig,
    PreconditionCatalog,
    SignalCatalog,
)
from ..hal.implementations.hal_manager import HalManager
from ..middleware.broker import InteractionBroker
from ..services.hmi_service import HmiService
from ..services.precondition_service import PreconditionService
from .hmi_keywords import HmiKeywords
from .state_keywords import StateKeywords


class ValidationFramework:
    """Main entry point exposed to Robot Framework."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    def __init__(self):
        self._logger = _create_logger()
        base_path = Path(__file__).resolve().parents[2] / "validation-framework" / "config"
        profile_name = BuiltIn().get_variable_value("${PROFILE}", default=None)
        profile_paths = []
        if profile_name:
            profile_paths.append(base_path / "profiles" / f"{profile_name}.yml")

        self._framework_config = FrameworkConfig.merge(base_path / "base.yml", profile_paths)
        self._signal_catalog = SignalCatalog.from_path(base_path / "interfaces" / "signals.yml")
        self._precondition_catalog = PreconditionCatalog.from_path(
            base_path / "interfaces" / "preconditions.yml"
        )

        self._hal_manager = HalManager(
            mode=self._framework_config.mode,
            config=self._framework_config.dict(),
            logger=self._logger,
        )

        self._broker = InteractionBroker(self._signal_catalog, self._hal_manager, self._logger)

        self.hmi = HmiKeywords(HmiService(self._broker))
        self.state = StateKeywords(
            PreconditionService(self._precondition_catalog, self._broker, self._logger)
        )

    def get_keyword_names(self):  # pragma: no cover - Robot Framework hook
        return self.hmi.get_keyword_names() + self.state.get_keyword_names()


def _create_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name or "validation_framework")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


__all__ = ["ValidationFramework"]
