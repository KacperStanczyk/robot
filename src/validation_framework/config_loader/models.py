"""Structured models and loading helpers for YAML configuration files."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml
from pydantic import BaseModel, Field, validator


class PayloadDefinition(BaseModel):
    """Definition of payload encoding details for a signal."""

    type: str = Field(..., description="The payload type, e.g. enum or numeric.")
    mapping: Dict[str, int] = Field(default_factory=dict)

    @validator("type")
    def validate_type(cls, value: str) -> str:
        if value not in {"enum", "uint", "int"}:
            raise ValueError(f"Unsupported payload type: {value!r}")
        return value


class SignalDefinition(BaseModel):
    """Configuration describing a CAN signal."""

    name: str
    bus: str
    can_id: int
    payload: PayloadDefinition

    @validator("can_id", pre=True)
    def parse_can_id(cls, value):
        if isinstance(value, str) and value.lower().startswith("0x"):
            return int(value, 16)
        return int(value)


class SignalCatalog(BaseModel):
    """Container for all configured signals."""

    signals: Dict[str, SignalDefinition]

    @classmethod
    def from_path(cls, path: Path) -> "SignalCatalog":
        data = yaml.safe_load(path.read_text())
        definitions: Dict[str, SignalDefinition] = {}
        for name, payload in data.get("signals", {}).items():
            definitions[name] = SignalDefinition(name=name, **payload)
        return cls(signals=definitions)

    def get(self, name: str) -> SignalDefinition:
        try:
            return self.signals[name]
        except KeyError as exc:
            raise KeyError(f"Signal {name!r} is not defined in the configuration") from exc


class PreconditionStep(BaseModel):
    """A single declarative step within a precondition."""

    action: str
    target: str
    value: Optional[str] = None


class PreconditionPolicy(BaseModel):
    """Time and safety policies applied to a precondition."""

    timeout: float = 30.0
    polling_interval: float = 1.0


class SafetyPolicy(BaseModel):
    abort_on_fault: bool = True


class PreconditionDefinition(BaseModel):
    """Complete description of a precondition."""

    name: str
    description: Optional[str]
    sla: PreconditionPolicy = Field(default_factory=PreconditionPolicy)
    safety: SafetyPolicy = Field(default_factory=SafetyPolicy)
    steps: List[PreconditionStep] = Field(default_factory=list)
    rollback: List[PreconditionStep] = Field(default_factory=list)


class PreconditionCatalog(BaseModel):
    preconditions: Dict[str, PreconditionDefinition]

    @classmethod
    def from_path(cls, path: Path) -> "PreconditionCatalog":
        data = yaml.safe_load(path.read_text())
        definitions: Dict[str, PreconditionDefinition] = {}
        for name, payload in data.get("preconditions", {}).items():
            definitions[name] = PreconditionDefinition(name=name, **payload)
        return cls(preconditions=definitions)

    def get(self, name: str) -> PreconditionDefinition:
        try:
            return self.preconditions[name]
        except KeyError as exc:
            raise KeyError(
                f"Precondition {name!r} is not defined in the configuration"
            ) from exc


class FrameworkConfig(BaseModel):
    mode: str
    timeouts: Dict[str, float] = Field(default_factory=dict)
    logging: Dict[str, Optional[str]] = Field(default_factory=dict)
    interfaces: Dict[str, Dict[str, Dict[str, str]]] = Field(default_factory=dict)

    @classmethod
    def merge(cls, base_path: Path, profile_paths: Iterable[Path]) -> "FrameworkConfig":
        base_data = yaml.safe_load(base_path.read_text())
        merged = dict(base_data)
        for profile_path in profile_paths:
            if not profile_path.exists():
                continue
            profile = yaml.safe_load(profile_path.read_text())
            merged = _deep_merge(merged, profile)
        return cls(**merged)


def _deep_merge(base: Dict, override: Dict) -> Dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


__all__ = [
    "FrameworkConfig",
    "PreconditionCatalog",
    "PreconditionDefinition",
    "PreconditionPolicy",
    "PreconditionStep",
    "SignalCatalog",
    "SignalDefinition",
]
