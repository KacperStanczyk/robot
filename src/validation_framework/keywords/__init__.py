"""Robot Framework entry point wiring together the validation stack."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, Optional

from robot.libraries.BuiltIn import BuiltIn

from ..config_loader.models import (
    FrameworkConfig,
    PreconditionCatalog,
    SignalCatalog,
)
from ..hal.implementations.hal_manager import HalManager
from ..middleware.broker import InteractionBroker
from ..services.domain_service import DomainService
from ..services.hmi_service import HmiService
from ..services.precondition_service import PreconditionService
from .domain_keywords import DomainKeywords
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

        self._preconditions = PreconditionService(
            self._precondition_catalog, self._broker, self._logger
        )
        self._domain_service = DomainService(self._broker, self._preconditions, self._logger)

        self.hmi = HmiKeywords(HmiService(self._domain_service))
        self.state = StateKeywords(self._preconditions)
        self.domain = DomainKeywords(self._domain_service)

        self._libraries = [self.hmi, self.state, self.domain]
        self._keywords: Dict[str, Callable[..., object]] = {}
        for library in self._libraries:
            for name, func in self._extract_keywords(library).items():
                self._keywords[name] = func
        self._keyword_lookup = {name.upper(): func for name, func in self._keywords.items()}

    def get_keyword_names(self):  # pragma: no cover - Robot Framework hook
        return list(self._keywords.keys())

    def run_keyword(self, name, args, kwargs=None):  # pragma: no cover - Robot hook
        kwargs = kwargs or {}
        try:
            func = self._keyword_lookup[name.upper()]
        except KeyError as exc:
            raise AttributeError(f"Unknown keyword: {name}") from exc
        return func(*args, **kwargs)

    def _extract_keywords(self, library):
        mapping: Dict[str, Callable[..., object]] = {}
        for attribute_name in dir(library):
            attribute = getattr(library, attribute_name)
            if callable(attribute):
                robot_name = getattr(attribute, "robot_name", None)
                if robot_name:
                    mapping[robot_name] = attribute
        if hasattr(library, "get_keyword_names"):
            for name in library.get_keyword_names():
                if name not in mapping:
                    method = getattr(library, name.replace(" ", "_").lower(), None)
                    if method:
                        mapping[name] = method
        return mapping


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
