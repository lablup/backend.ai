"""Domain wiring: the processors the domain adapter reads, and the domain's seeds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainInput,
    DeleteDomainInput,
    PurgeDomainInput,
    RestoreDomainInput,
)
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.creators import DomainCreator
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService
from ai.backend.testutils.scenario import Seed
from bai_kit.manager.runner import SeedContext, Wired, WiringDeps

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors  # pants: no-infer-dep


@dataclass
class DomainAdapterProcessors:
    """The two groups ``DomainAdapter`` reads off the ``Processors`` bundle."""

    domain: DomainProcessors
    resource_group: ResourceGroupProcessors


DISPATCH: dict[type, str] = {
    CreateDomainInput: "admin_create",
    AdminSearchDomainsInput: "admin_search",
    DeleteDomainInput: "admin_delete",
    RestoreDomainInput: "admin_restore",
    PurgeDomainInput: "admin_purge",
    # UpdateDomainInput needs the name beside it: Call("admin_update", name, input).
    # get() takes no DTO: Call("get", name).
}


def domain_wiring(deps: WiringDeps) -> Wired:
    provider = V2DBOpsProvider(deps.engine)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=deps.monitors,
            validators=deps.v2_validators,
            repository=OpsRepository(provider),
        )
    )
    domain = DomainProcessors(
        registry.group(GroupMeta(DOMAIN_ENTITY_TYPE)),
        DomainService(DomainRepository(deps.engine, provider)),
        [],
    )
    resource_group = ResourceGroupProcessors(
        registry.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)),
        ResourceGroupService(ResourceGroupRepository(deps.engine, provider)),
    )
    adapter = DomainAdapter(cast("Processors", DomainAdapterProcessors(domain, resource_group)))
    return Wired(
        adapter=adapter,
        dispatch=DISPATCH,
        client_attr="domain",
    )


def create_input(**overrides: Any) -> CreateDomainInput:
    """The smallest valid create input; override what the scenario is about."""
    values: dict[str, Any] = {"name": "d1"}
    values.update(overrides)
    return CreateDomainInput(**values)


def seed_domain(name: str, **overrides: Any) -> Seed:
    """A domain laid down through the same Creator the adapter uses (grade 1)."""

    async def build(ctx: SeedContext) -> DomainData:
        data: DomainData = await ctx.ops.create_role_managed_global_entity(
            DomainCreator(name=name, **overrides)
        )
        return data

    return Seed(label=name, build=build)
