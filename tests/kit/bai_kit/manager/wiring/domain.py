"""Domain wiring: the processors the domain adapter reads, and the domain's seeds."""

from __future__ import annotations

from typing import Any

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainInput,
    DeleteDomainInput,
    PurgeDomainInput,
    RestoreDomainInput,
    UpdateDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import DomainPayload
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.data.domain.types import DomainData, UserInfo
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
from ai.backend.testutils.typed_scenario import ActorBound, needs_actor, op
from bai_kit.manager.runner import SeedContext, Wired, WiringDeps

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
        registry.group(GroupMeta(DomainEntityType())),
        DomainService(DomainRepository(deps.engine, provider)),
        [],
    )
    resource_group = ResourceGroupProcessors(
        registry.group(GroupMeta(ResourceGroupEntityType())),
        ResourceGroupService(ResourceGroupRepository(deps.engine, provider)),
    )
    adapter = DomainAdapter(domain, resource_group)
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


# ---------------------------------------------------------------------------
# The operations a domain scenario may name, bound from the adapter's own methods
# ---------------------------------------------------------------------------

get_domain = op(DomainAdapter.get)
admin_search = op(DomainAdapter.admin_search)
admin_delete = op(DomainAdapter.admin_delete)
admin_restore = op(DomainAdapter.admin_restore)
admin_purge = op(DomainAdapter.admin_purge)
_admin_create = op(DomainAdapter.admin_create)
_admin_update = op(DomainAdapter.admin_update)


def admin_create(request: CreateDomainInput) -> ActorBound[DomainAdapter, DomainPayload, UserInfo]:
    """Creating a domain records who asked, so the call waits for the actor."""
    return needs_actor(lambda actor: _admin_create(request, actor))


def admin_update(
    name: str, request: UpdateDomainInput
) -> ActorBound[DomainAdapter, DomainPayload, UserInfo]:
    """Editing a domain records who asked, as creating one does."""
    return needs_actor(lambda actor: _admin_update(name, request, actor))
