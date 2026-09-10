"""Write specs for a resource group."""

from __future__ import annotations

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.resource_group.creators import (
    ResourceGroupCreator,
    ResourceGroupForDomainRelationCreator,
    ResourceGroupForKeypairRelationCreator,
    ResourceGroupForProjectRelationCreator,
)
from bai_scenario.seeds.seeder import Link, Spec


def seed_resource_group(
    *, name_hint: str = "resource-group", scheduler: str = "fifo"
) -> Spec[ResourceGroupData]:
    """The scope agents and sessions are created under."""

    def build(name: str) -> ResourceGroupCreator:
        return ResourceGroupCreator(name=name, driver="static", scheduler=scheduler)

    return Spec("a resource group", name_hint, build)


def link_to_domain() -> Link[DomainData, ResourceGroupData]:
    """Every session of that domain may schedule on the group."""
    return Link(
        kind="is allowed for",
        creator=ResourceGroupForDomainRelationCreator(),
        scope_id=lambda domain: domain.id,
        target_id=lambda group: ResourceGroupID(group.id),
    )


def link_to_project() -> Link[ProjectData, ResourceGroupData]:
    """Every session of that project may schedule on the group."""
    return Link(
        kind="is allowed for",
        creator=ResourceGroupForProjectRelationCreator(),
        scope_id=lambda project: ProjectID(project.id),
        target_id=lambda group: ResourceGroupID(group.id),
    )


def link_to_keypair(access_key: str) -> Link[UserData, ResourceGroupData]:
    """Only sessions asked for with that key may schedule on the group."""
    return Link(
        kind="is allowed for the key of",
        creator=ResourceGroupForKeypairRelationCreator(access_key=AccessKey(access_key)),
        scope_id=lambda user: UserID(user.id),
        target_id=lambda group: ResourceGroupID(group.id),
    )
