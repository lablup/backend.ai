from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
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
