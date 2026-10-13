from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from typing import Any, override

from pydantic import Field

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.data.resource_group.types import SchedulerType
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_group.upserters import ResourceGroupUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class ResourceGroupSeed(SeedItem):
    """One ``scaling_groups`` row. The domains and projects it is allowed to are not
    written here."""

    id: ResourceGroupID
    name: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=512)
    is_active: bool = True
    is_public: bool = True
    is_default: bool = False
    wsproxy_addr: str | None = Field(default=None, max_length=1024)
    wsproxy_api_token: str | None = Field(default=None, max_length=128)
    driver: str = Field(min_length=1, max_length=64)
    driver_opts: dict[str, Any] = {}
    scheduler: str = Field(min_length=1, max_length=64)
    scheduler_opts: ResourceGroupOpts = ResourceGroupOpts()
    use_host_network: bool = False

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=ResourceGroupUpserter(
                id=self.id,
                name=self.name,
                description=self.description,
                is_active=self.is_active,
                is_public=self.is_public,
                is_default=self.is_default,
                wsproxy_addr=self.wsproxy_addr,
                wsproxy_api_token=self.wsproxy_api_token,
                driver=self.driver,
                driver_opts=self.driver_opts,
                scheduler=self.scheduler,
                scheduler_opts=self.scheduler_opts,
                use_host_network=self.use_host_network,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        """The rules the API applies to the name, the scheduler and the preemption runtime."""
        failures: list[str] = []
        if not self.name.strip():
            failures.append("name is blank")
        schedulers = sorted(scheduler.value for scheduler in SchedulerType)
        if self.scheduler not in schedulers:
            failures.append(f"scheduler {self.scheduler!r} is not one of {schedulers}")
        if self.scheduler_opts.preemption.preemption_min_runtime < timedelta(0):
            failures.append("scheduler_opts.preemption.preemption_min_runtime is negative")
        return failures

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ResourceGroupSeed]]) -> list[SeedRejection]:
        """None: the constraints on ``scaling_groups`` fail an item that repeats a name or
        a second default."""
        return []
