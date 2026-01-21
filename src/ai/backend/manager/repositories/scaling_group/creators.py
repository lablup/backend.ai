from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.common.types import AccessKey
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupOpts,
    ScalingGroupRow,
)
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ScalingGroupCreatorSpec(CreatorSpec[ScalingGroupRow]):
    """CreatorSpec for scaling group."""

    name: str
    driver: str
    scheduler: str
    description: Optional[str] = None
    is_active: bool = True
    is_public: bool = True
    wsproxy_addr: Optional[str] = None
    wsproxy_api_token: Optional[str] = None
    driver_opts: Mapping[str, Any] = field(default_factory=dict)
    scheduler_opts: Optional[ScalingGroupOpts] = None
    use_host_network: bool = False

    @override
    def build_row(self) -> ScalingGroupRow:
        return ScalingGroupRow(
            name=self.name,
            description=self.description,
            is_active=self.is_active,
            is_public=self.is_public,
            wsproxy_addr=self.wsproxy_addr,
            wsproxy_api_token=self.wsproxy_api_token,
            driver=self.driver,
            driver_opts=dict(self.driver_opts),
            scheduler=self.scheduler,
            scheduler_opts=self.scheduler_opts if self.scheduler_opts else ScalingGroupOpts(),
            use_host_network=self.use_host_network,
        )


@dataclass
class ScalingGroupForDomainCreatorSpec(CreatorSpec[ScalingGroupForDomainRow]):
    """CreatorSpec for associating a scaling group with a domain."""

    scaling_group: str
    domain: str

    @override
    def build_row(self) -> ScalingGroupForDomainRow:
        return ScalingGroupForDomainRow(
            scaling_group=self.scaling_group,
            domain=self.domain,
        )


@dataclass
class ScalingGroupForKeypairsCreatorSpec(CreatorSpec[ScalingGroupForKeypairsRow]):
    """CreatorSpec for associating a scaling group with a keypair."""

    scaling_group: str
    access_key: AccessKey

    @override
    def build_row(self) -> ScalingGroupForKeypairsRow:
        return ScalingGroupForKeypairsRow(
            scaling_group=self.scaling_group,
            access_key=self.access_key,
        )


@dataclass
class ScalingGroupForProjectCreatorSpec(CreatorSpec[ScalingGroupForProjectRow]):
    """CreatorSpec for associating a scaling group with a project (user group)."""

    scaling_group: str
    project: UUID

    @override
    def build_row(self) -> ScalingGroupForProjectRow:
        return ScalingGroupForProjectRow(
            scaling_group=self.scaling_group,
            group=self.project,
        )
