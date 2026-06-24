from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.data.idle_checker.types import CheckerType
from ai.backend.manager.models.base import ABCColumnPayload

_DISCRIMINATOR_KEY = "checker_type"


class IdleCheckerSpecABC(ABCColumnPayload):
    """Config payload stored in ``idle_checkers.spec``; ``load`` dispatches by ``checker_type``
    to a concrete spec. Concrete spec fields land with the checker-logic stories."""

    @override
    def serialize(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    @override
    def load(cls, raw: dict[str, Any]) -> IdleCheckerSpecABC:
        match CheckerType(raw[_DISCRIMINATOR_KEY]):
            case CheckerType.SESSION_LIFETIME:
                return SessionLifetimeSpec.from_raw(raw)
            case CheckerType.NETWORK_TIMEOUT:
                return NetworkTimeoutSpec.from_raw(raw)
            case CheckerType.UTILIZATION:
                return UtilizationSpec.from_raw(raw)


@dataclass(frozen=True)
class SessionLifetimeSpec(IdleCheckerSpecABC):
    @classmethod
    def from_raw(cls, _raw: dict[str, Any]) -> SessionLifetimeSpec:
        return cls()

    @override
    def serialize(self) -> dict[str, Any]:
        return {_DISCRIMINATOR_KEY: CheckerType.SESSION_LIFETIME.value}


@dataclass(frozen=True)
class NetworkTimeoutSpec(IdleCheckerSpecABC):
    @classmethod
    def from_raw(cls, _raw: dict[str, Any]) -> NetworkTimeoutSpec:
        return cls()

    @override
    def serialize(self) -> dict[str, Any]:
        return {_DISCRIMINATOR_KEY: CheckerType.NETWORK_TIMEOUT.value}


@dataclass(frozen=True)
class UtilizationSpec(IdleCheckerSpecABC):
    @classmethod
    def from_raw(cls, _raw: dict[str, Any]) -> UtilizationSpec:
        return cls()

    @override
    def serialize(self) -> dict[str, Any]:
        return {_DISCRIMINATOR_KEY: CheckerType.UTILIZATION.value}
