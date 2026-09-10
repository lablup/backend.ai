"""Write specs for a resource group."""

from __future__ import annotations

from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.creators import ResourceGroupCreator
from bai_scenario.seeds.seeder import Spec


def seed_resource_group(
    *, name_hint: str = "resource-group", scheduler: str = "fifo"
) -> Spec[ResourceGroupData]:
    """The scope agents and sessions are created under."""

    def build(name: str) -> ResourceGroupCreator:
        return ResourceGroupCreator(name=name, driver="static", scheduler=scheduler)

    return Spec("a resource group", name_hint, build)
