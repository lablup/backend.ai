from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ai.backend.common.identifier.domain import DomainID, DomainName

__all__ = (
    "DomainFactory",
    "DomainFixtureData",
)


@dataclass(frozen=True)
class DomainFixtureData:
    domain_name: DomainName
    domain_id: DomainID


DomainFactory = Callable[..., Awaitable[DomainFixtureData]]
