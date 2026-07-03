from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ai.backend.common.identifier.domain import DomainID, DomainName
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName

__all__ = (
    "DomainFactory",
    "DomainFixtureData",
    "ScalingGroupFixtureData",
)


@dataclass(frozen=True)
class DomainFixtureData:
    domain_name: DomainName
    domain_id: DomainID


@dataclass(frozen=True)
class ScalingGroupFixtureData:
    scaling_group_name: ResourceGroupName
    scaling_group_id: ResourceGroupID


DomainFactory = Callable[..., Awaitable[DomainFixtureData]]
