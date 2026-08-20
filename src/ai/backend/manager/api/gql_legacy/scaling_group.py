from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
)

import graphene
import graphene_federation
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.engine.row import Row

from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import AccessKey, ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
    ResourceGroupOpts,
    ResourceGroupRow,
    resource_groups,
    sgroups_for_domains,
    sgroups_for_groups,
    sgroups_for_keypairs,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base.creator import BulkCreator, Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.base.rbac.scope_binder import (
    RBACScopeBinder,
    RBACScopeBindingPair,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.resource_group.creators import (
    ResourceGroupCreatorSpec,
    ResourceGroupForDomainCreatorSpec,
    ResourceGroupForKeypairsCreatorSpec,
    ResourceGroupForProjectCreatorSpec,
)
from ai.backend.manager.repositories.resource_group.purgers import (
    ResourceGroupNamePurgerSpec,
    create_resource_group_for_keypairs_purger,
)
from ai.backend.manager.repositories.resource_group.scope_binders import (
    ResourceGroupDomainEntityUnbinder,
    ResourceGroupProjectEntityUnbinder,
)
from ai.backend.manager.repositories.resource_group.updaters import (
    ResourceGroupDriverConfigUpdaterSpec,
    ResourceGroupMetadataUpdaterSpec,
    ResourceGroupNetworkConfigUpdaterSpec,
    ResourceGroupSchedulerConfigUpdaterSpec,
    ResourceGroupStatusUpdaterSpec,
    ResourceGroupUpdaterSpec,
)
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.resource_group.actions.associate_with_domain import (
    AssociateResourceGroupWithDomainsAction,
)
from ai.backend.manager.services.resource_group.actions.associate_with_keypair import (
    AssociateResourceGroupWithKeypairsAction,
)
from ai.backend.manager.services.resource_group.actions.associate_with_user_group import (
    AssociateResourceGroupWithUserGroupsAction,
)
from ai.backend.manager.services.resource_group.actions.create import (
    CreateResourceGroupAction,
)
from ai.backend.manager.services.resource_group.actions.disassociate_with_domain import (
    DisassociateResourceGroupWithDomainsAction,
)
from ai.backend.manager.services.resource_group.actions.disassociate_with_keypair import (
    DisassociateResourceGroupWithKeypairsAction,
)
from ai.backend.manager.services.resource_group.actions.disassociate_with_user_group import (
    DisassociateResourceGroupWithUserGroupsAction,
)
from ai.backend.manager.services.resource_group.actions.lookup import LookupResourceGroupAction
from ai.backend.manager.services.resource_group.actions.purge_resource_group import (
    PurgeResourceGroupAction,
)
from ai.backend.manager.services.resource_group.actions.update import (
    UpdateResourceGroupAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import (
    batch_multiresult,
    batch_multiresult_in_scalar_stream,
    batch_result,
)
from .gql_relay import (
    AsyncNode,
    Connection,
)

if TYPE_CHECKING:
    from .schema import GraphQueryContext

__all__ = (
    "AssociateScalingGroupWithDomain",
    "AssociateScalingGroupWithKeyPair",
    "AssociateScalingGroupWithUserGroup",
    "AssociateScalingGroupsWithDomain",
    "AssociateScalingGroupsWithKeyPair",
    "AssociateScalingGroupsWithUserGroup",
    "CreateScalingGroup",
    "DeleteScalingGroup",
    "DisassociateAllScalingGroupsWithDomain",
    "DisassociateAllScalingGroupsWithGroup",
    "DisassociateScalingGroupWithDomain",
    "DisassociateScalingGroupWithKeyPair",
    "DisassociateScalingGroupWithUserGroup",
    "DisassociateScalingGroupsWithDomain",
    "DisassociateScalingGroupsWithKeyPair",
    "DisassociateScalingGroupsWithUserGroup",
    "ModifyScalingGroup",
    "ScalingGroup",
    "ScalingGroupConnection",
    "ScalingGroupNode",
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


async def _resolve_resource_group_id(
    graph_ctx: GraphQueryContext,
    scaling_group: str,
) -> ResourceGroupID:
    result = await graph_ctx.processors.resource_group.lookup.run(
        LookupResourceGroupAction(name=ResourceGroupName(scaling_group))
    )
    return result.data.id


async def _resolve_resource_group_ids(
    graph_ctx: GraphQueryContext,
    scaling_groups: Sequence[str],
) -> list[ResourceGroupID]:
    return [await _resolve_resource_group_id(graph_ctx, name) for name in scaling_groups]


@graphene_federation.key("id")
class ScalingGroupNode(graphene.ObjectType):  # type: ignore[misc]
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.12.0."

    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    is_public = graphene.Boolean()
    created_at = GQLDateTime()
    wsproxy_addr = graphene.String()
    wsproxy_api_token = graphene.String()
    driver = graphene.String()
    driver_opts = graphene.JSONString()
    scheduler = graphene.String()
    scheduler_opts = graphene.JSONString()
    use_host_network = graphene.Boolean()

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: ResourceGroupRow,
    ) -> Self:
        return cls(
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            is_public=row.is_public,
            created_at=row.created_at,
            wsproxy_addr=row.wsproxy_addr,
            wsproxy_api_token=row.wsproxy_api_token,
            driver=row.driver,
            driver_opts=row.driver_opts,
            scheduler=row.scheduler,
            scheduler_opts=row.scheduler_opts,
            use_host_network=row.use_host_network,
        )

    # TODO: Refactor with action-processor structure, check permission
    async def __resolve_reference(
        self, info: graphene.ResolveInfo, **kwargs: Any
    ) -> ScalingGroupNode:
        _, scaling_group_name = AsyncNode.resolve_global_id(info, self.id)
        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_readonly_session() as db_session:
            query_stmt = sa.select(ResourceGroupRow).where(
                ResourceGroupRow.name == scaling_group_name
            )
            result = await db_session.scalar(query_stmt)
            if result is None:
                raise ResourceGroupNotFound(f"Scaling group not found: {scaling_group_name}")
            return ScalingGroupNode.from_row(graph_ctx, result)

    @classmethod
    async def batch_load_by_group(
        cls,
        ctx: GraphQueryContext,
        group_ids: Sequence[uuid.UUID],
    ) -> Sequence[Sequence[ScalingGroupNode]]:
        j = sa.join(
            ResourceGroupRow,
            ResourceGroupForProjectRow,
            ResourceGroupRow.id == ResourceGroupForProjectRow.resource_group_id,
        )
        _stmt = (
            sa.select(ResourceGroupRow)
            .select_from(j)
            .where(ResourceGroupForProjectRow.group.in_(group_ids))
        )
        async with ctx.db.begin_readonly_session() as db_session:
            return await batch_multiresult_in_scalar_stream(
                ctx,
                db_session,
                _stmt,
                cls,
                group_ids,
                lambda row: row.name,
            )

    @classmethod
    async def batch_load_by_domain(
        cls,
        ctx: GraphQueryContext,
        domain_names: Sequence[str],
    ) -> Sequence[Sequence[ScalingGroupNode]]:
        j = sa.join(
            ResourceGroupRow,
            ResourceGroupForDomainRow,
            ResourceGroupRow.id == ResourceGroupForDomainRow.resource_group_id,
        ).join(DomainRow, DomainRow.id == ResourceGroupForDomainRow.domain_id)
        _stmt = sa.select(ResourceGroupRow).select_from(j).where(DomainRow.name.in_(domain_names))
        async with ctx.db.begin_readonly_session() as db_session:
            return await batch_multiresult_in_scalar_stream(
                ctx,
                db_session,
                _stmt,
                cls,
                domain_names,
                lambda row: row.name,
            )

    @classmethod
    async def batch_load_by_keypair(
        cls,
        ctx: GraphQueryContext,
        access_keys: Sequence[AccessKey],
    ) -> Sequence[Sequence[ScalingGroupNode]]:
        j = sa.join(
            ResourceGroupRow,
            ResourceGroupForKeypairsRow,
            ResourceGroupRow.id == ResourceGroupForKeypairsRow.resource_group_id,
        )
        _stmt = (
            sa.select(ResourceGroupRow)
            .select_from(j)
            .where(ResourceGroupForKeypairsRow.access_key.in_(access_keys))
        )
        async with ctx.db.begin_readonly_session() as db_session:
            return await batch_multiresult_in_scalar_stream(
                ctx,
                db_session,
                _stmt,
                cls,
                access_keys,
                lambda row: row.name,
            )


class ScalingGroupConnection(Connection):
    class Meta:
        node = ScalingGroupNode
        description = "Added in 24.12.0."


class ScalingGroup(graphene.ObjectType):  # type: ignore[misc]
    name = graphene.String()
    description = graphene.String()
    is_active = graphene.Boolean()
    is_public = graphene.Boolean()
    created_at = GQLDateTime()
    wsproxy_addr = graphene.String()
    wsproxy_api_token = graphene.String()
    driver = graphene.String()
    driver_opts = graphene.JSONString()
    scheduler = graphene.String()
    scheduler_opts = graphene.JSONString()
    use_host_network = graphene.Boolean()
    accelerator_quantum_size = graphene.Field(
        graphene.Float,
        description="Added in 25.5.0.",
    )

    # Dynamic fields.
    agent_count_by_status = graphene.Field(
        graphene.Int,
        description="Added in 24.03.7.",
        status=graphene.String(
            default_value=AgentStatus.ALIVE.name,
            description=f"Possible states of an agent. Should be one of {[s.name for s in AgentStatus]}. Default is 'ALIVE'.",
        ),
    )

    agent_total_resource_slots_by_status = graphene.Field(
        graphene.JSONString,
        description="Added in 24.03.7.",
        status=graphene.String(
            default_value=AgentStatus.ALIVE.name,
            description=f"Possible states of an agent. Should be one of {[s.name for s in AgentStatus]}. Default is 'ALIVE'.",
        ),
    )
    resource_allocation_limit_for_sessions = graphene.JSONString(
        description="Added in 25.6.0. The limit of computing resources that can be allocated to each compute session created within this resource group.",
    )

    # TODO: Replace this field with a generic resource slot query API
    own_session_occupied_resource_slots = graphene.Field(
        graphene.JSONString,
        description=(
            "Added in 25.4.0. The sum of occupied slots across compute sessions that occupying agent's resources. "
            "Only includes sessions owned by the user."
        ),
    )

    def __init__(self, is_masked: bool = False, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._is_masked = is_masked

    async def resolve_agent_count_by_status(
        self, info: graphene.ResolveInfo, status: str = AgentStatus.ALIVE.name
    ) -> int | None:
        if self._is_masked:
            return None
        from .agent import Agent

        return await Agent.load_count(
            info.context,
            raw_status=status,
            scaling_group=self.name,
        )

    async def resolve_agent_total_resource_slots_by_status(
        self, info: graphene.ResolveInfo, status: str = AgentStatus.ALIVE.name
    ) -> Mapping[str, Any] | None:
        if self._is_masked:
            return None
        from ai.backend.manager.data.agent.types import AgentStatus
        from ai.backend.manager.models.agent.row import AgentRow
        from ai.backend.manager.models.resource_slot import AgentResourceRow

        graph_ctx = info.context
        async with graph_ctx.db.begin_readonly_session() as db_session:
            j = sa.join(AgentResourceRow, AgentRow, AgentResourceRow.agent_id == AgentRow.id)
            query = (
                sa.select(
                    AgentResourceRow.slot_name,
                    sa.func.sum(AgentResourceRow.capacity).label("total_capacity"),
                    sa.func.sum(AgentResourceRow.used).label("total_used"),
                )
                .select_from(j)
                .where(
                    (AgentRow.scaling_group == self.name) & (AgentRow.status == AgentStatus[status])
                )
                .group_by(AgentResourceRow.slot_name)
            )
            result = await db_session.execute(query)

            total_occupied_slots = ResourceSlot()
            total_available_slots = ResourceSlot()
            for row in result:
                total_available_slots[row.slot_name] = row.total_capacity
                total_occupied_slots[row.slot_name] = row.total_used

            return {
                "occupied_slots": total_occupied_slots.to_json(),
                "available_slots": total_available_slots.to_json(),
            }

    async def resolve_resource_allocation_limit_for_sessions(
        self, info: graphene.ResolveInfo
    ) -> dict[str, Any]:
        from ai.backend.manager.models.agent import AgentRow

        # TODO: Allow admins to set which value to return here among "min", "max", "custom"
        graph_ctx: GraphQueryContext = info.context
        agent_list = await AgentRow.get_schedulable_agents_by_sgroup(self.name, db=graph_ctx.db)

        def _compare_each_resource_and_get_max(
            val1: ResourceSlot, val2: ResourceSlot | None
        ) -> ResourceSlot:
            if val2 is None:
                return val1
            return_val = ResourceSlot()
            val1.sync_keys(val2)
            for key in val1:
                return_val[key] = max(val1[key], val2[key])
            return return_val

        result: ResourceSlot | None = None
        for agent_row in agent_list:
            result = _compare_each_resource_and_get_max(agent_row.available_slots, result)
        if result is None:
            return {}
        return {k: v for k, v in result.to_json().items() if v != "0"}

    # TODO: Replace this field with a generic resource slot query API
    async def resolve_own_session_occupied_resource_slots(
        self, info: graphene.ResolveInfo
    ) -> Mapping[str, Any]:
        from ai.backend.manager.models.agent.row import AgentRow
        from ai.backend.manager.models.kernel import KernelRow
        from ai.backend.manager.models.resource_slot import ResourceAllocationRow

        graph_ctx: GraphQueryContext = info.context
        user = graph_ctx.user
        j = sa.join(
            ResourceAllocationRow, KernelRow, ResourceAllocationRow.kernel_id == KernelRow.id
        ).join(AgentRow, KernelRow.agent == AgentRow.id)
        query = (
            sa.select(
                ResourceAllocationRow.slot_name,
                sa.func.sum(ResourceAllocationRow.used).label("total"),
            )
            .select_from(j)
            .where(
                sa.and_(
                    ResourceAllocationRow.free_at.is_(None),
                    KernelRow.user_uuid == user["uuid"],
                    AgentRow.scaling_group == self.name,
                )
            )
            .group_by(ResourceAllocationRow.slot_name)
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            result = await db_session.execute(query)
        occupied_slots = ResourceSlot()
        for row in result:
            if row.total is not None:
                occupied_slots[row.slot_name] = row.total
        return occupied_slots.to_json()

    async def resolve_accelerator_quantum_size(self, info: graphene.ResolveInfo) -> float | None:
        graph_ctx: GraphQueryContext = info.context
        result = await graph_ctx.etcd.get("config/plugins/accelerator/cuda/quantum_size")
        return float(result) if result is not None else None

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row[Any] | None,
    ) -> ScalingGroup | None:
        if row is None:
            return None
        return cls(
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            is_public=row.is_public,
            created_at=row.created_at,
            wsproxy_addr=row.wsproxy_addr,
            wsproxy_api_token=row.wsproxy_api_token,
            driver=row.driver,
            driver_opts=row.driver_opts,
            scheduler=row.scheduler,
            scheduler_opts=row.scheduler_opts.model_dump(mode="json"),
            use_host_network=row.use_host_network,
        )

    @classmethod
    def from_orm_row(
        cls,
        row: ResourceGroupRow,
    ) -> ScalingGroup:
        return cls(
            name=row.name,
            description=row.description,
            is_active=row.is_active,
            is_public=row.is_public,
            created_at=row.created_at,
            wsproxy_addr=row.wsproxy_addr,
            wsproxy_api_token=row.wsproxy_api_token,
            driver=row.driver,
            driver_opts=row.driver_opts,
            scheduler=row.scheduler,
            scheduler_opts=row.scheduler_opts.model_dump(mode="json"),
            use_host_network=row.use_host_network,
        )

    @property
    def masked(self) -> Self:
        return self.__class__(
            is_masked=True,
            name=self.name,
            is_active=self.is_active,
            own_session_occupied_resource_slots=self.own_session_occupied_resource_slots,
            accelerator_quantum_size=self.accelerator_quantum_size,
        )

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        is_active: bool | None = None,
    ) -> Sequence[ScalingGroup]:
        query = sa.select(resource_groups).select_from(resource_groups)
        if is_active is not None:
            query = query.where(resource_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def load_by_domain(
        cls,
        ctx: GraphQueryContext,
        domain: str,
        *,
        is_active: bool | None = None,
    ) -> Sequence[ScalingGroup]:
        j = sa.join(
            resource_groups,
            sgroups_for_domains,
            resource_groups.c.id == sgroups_for_domains.c.resource_group_id,
        )
        query = (
            sa.select(resource_groups)
            .select_from(j)
            .where(
                sgroups_for_domains.c.domain_id
                == sa.select(DomainRow.id).where(DomainRow.name == domain).scalar_subquery()
            )
        )
        if is_active is not None:
            query = query.where(resource_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def load_by_group(
        cls,
        ctx: GraphQueryContext,
        group: uuid.UUID,
        *,
        is_active: bool | None = None,
    ) -> Sequence[ScalingGroup]:
        j = sa.join(
            resource_groups,
            sgroups_for_groups,
            resource_groups.c.id == sgroups_for_groups.c.resource_group_id,
        )
        query = sa.select(resource_groups).select_from(j).where(sgroups_for_groups.c.group == group)
        if is_active is not None:
            query = query.where(resource_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def load_by_keypair(
        cls,
        ctx: GraphQueryContext,
        access_key: str,
        *,
        is_active: bool | None = None,
    ) -> Sequence[ScalingGroup]:
        j = sa.join(
            resource_groups,
            sgroups_for_keypairs,
            resource_groups.c.id == sgroups_for_keypairs.c.resource_group_id,
        )
        query = (
            sa.select(resource_groups)
            .select_from(j)
            .where(sgroups_for_keypairs.c.access_key == access_key)
        )
        if is_active is not None:
            query = query.where(resource_groups.c.is_active == is_active)
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for row in (await conn.stream(query))
                if (obj := cls.from_row(ctx, row)) is not None
            ]

    @classmethod
    async def batch_load_by_group(
        cls,
        ctx: GraphQueryContext,
        group_ids: Sequence[uuid.UUID],
    ) -> Sequence[Sequence[ScalingGroup | None]]:
        j = sa.join(
            resource_groups,
            sgroups_for_groups,
            resource_groups.c.id == sgroups_for_groups.c.resource_group_id,
        )
        query = (
            sa.select(resource_groups, sgroups_for_groups.c.group)
            .select_from(j)
            .where(sgroups_for_groups.c.group.in_(group_ids))
        )
        async with ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                ctx,
                conn,
                query,
                cls,
                group_ids,
                lambda row: row.group,
            )

    @classmethod
    async def batch_load_by_name(
        cls,
        ctx: GraphQueryContext,
        names: Sequence[str],
    ) -> Sequence[ScalingGroup | None]:
        query = (
            sa.select(resource_groups)
            .select_from(resource_groups)
            .where(resource_groups.c.name.in_(names))
        )
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                names,
                lambda row: row.name,
            )


class CreateScalingGroupInput(graphene.InputObjectType):  # type: ignore[misc]
    description = graphene.String(required=False, default_value="")
    is_active = graphene.Boolean(required=False, default_value=True)
    is_public = graphene.Boolean(required=False, default_value=True)
    wsproxy_addr = graphene.String(required=False, default_value=None)
    wsproxy_api_token = graphene.String(required=False, default_value=None)
    driver = graphene.String(required=True)
    driver_opts = graphene.JSONString(required=False, default_value={})
    scheduler = graphene.String(required=True)
    scheduler_opts = graphene.JSONString(required=False, default_value={})
    use_host_network = graphene.Boolean(required=False, default_value=False)


class ModifyScalingGroupInput(graphene.InputObjectType):  # type: ignore[misc]
    description = graphene.String(required=False)
    is_active = graphene.Boolean(required=False)
    is_public = graphene.Boolean(required=False)
    wsproxy_addr = graphene.String(required=False)
    wsproxy_api_token = graphene.String(required=False)
    driver = graphene.String(required=False)
    driver_opts = graphene.JSONString(required=False)
    scheduler = graphene.String(required=False)
    scheduler_opts = graphene.JSONString(required=False)
    use_host_network = graphene.Boolean(required=False)

    def to_updater(self, name: str) -> Updater[ResourceGroupRow]:
        """Convert GraphQL input to Updater for scaling group modification."""
        status_spec = ResourceGroupStatusUpdaterSpec(
            is_active=OptionalState.from_graphql(self.is_active),
            is_public=OptionalState.from_graphql(self.is_public),
        )
        metadata_spec = ResourceGroupMetadataUpdaterSpec(
            description=TriState.from_graphql(self.description),
        )
        network_spec = ResourceGroupNetworkConfigUpdaterSpec(
            wsproxy_addr=TriState.from_graphql(self.wsproxy_addr),
            wsproxy_api_token=TriState.from_graphql(self.wsproxy_api_token),
            use_host_network=OptionalState.from_graphql(self.use_host_network),
        )
        driver_spec = ResourceGroupDriverConfigUpdaterSpec(
            driver=OptionalState.from_graphql(self.driver),
            driver_opts=OptionalState.from_graphql(self.driver_opts),
        )
        scheduler_spec = ResourceGroupSchedulerConfigUpdaterSpec(
            scheduler=OptionalState.from_graphql(self.scheduler),
            scheduler_opts=OptionalState.from_graphql(
                ResourceGroupOpts.model_validate(self.scheduler_opts)
                if self.scheduler_opts is not None and self.scheduler_opts is not Undefined
                else Undefined
            ),
        )
        spec = ResourceGroupUpdaterSpec(
            status=status_spec,
            metadata=metadata_spec,
            network=network_spec,
            driver=driver_spec,
            scheduler=scheduler_spec,
        )
        return Updater(spec=spec, pk_value=name)


class CreateScalingGroup(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = CreateScalingGroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    scaling_group = graphene.Field(lambda: ScalingGroup, required=False)

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
        props: CreateScalingGroupInput,
    ) -> CreateScalingGroup:
        graph_ctx: GraphQueryContext = info.context
        spec = ResourceGroupCreatorSpec(
            name=name,
            description=props.description,
            is_active=bool(props.is_active),
            is_public=bool(props.is_public),
            wsproxy_addr=props.wsproxy_addr,
            wsproxy_api_token=props.wsproxy_api_token,
            driver=props.driver,
            driver_opts=props.driver_opts,
            scheduler=props.scheduler,
            scheduler_opts=ResourceGroupOpts.model_validate(props.scheduler_opts),
            use_host_network=bool(props.use_host_network),
        )
        creator = Creator(spec=spec)
        action = CreateResourceGroupAction(creator=creator)
        result = await graph_ctx.processors.resource_group.create_resource_group.run(action)
        return cls(
            ok=True,
            msg="success",
            scaling_group=ScalingGroup(
                name=result.resource_group.name,
                description=result.resource_group.metadata.description,
                is_active=result.resource_group.status.is_active,
                is_public=result.resource_group.status.is_public,
                created_at=result.resource_group.metadata.created_at,
                wsproxy_addr=result.resource_group.network.wsproxy_addr,
                wsproxy_api_token=result.resource_group.network.wsproxy_api_token,
                driver=result.resource_group.driver.name,
                driver_opts=dict(result.resource_group.driver.options),
                scheduler=result.resource_group.scheduler.name.value,
                scheduler_opts=result.resource_group.scheduler.options.to_json(),
                use_host_network=result.resource_group.network.use_host_network,
            ),
        )


class ModifyScalingGroup(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)
        props = ModifyScalingGroupInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
        props: ModifyScalingGroupInput,
    ) -> ModifyScalingGroup:
        graph_ctx: GraphQueryContext = info.context
        resource_group_id = await _resolve_resource_group_id(graph_ctx, name)
        await graph_ctx.processors.resource_group.update_resource_group.run(
            UpdateResourceGroupAction(
                resource_group_id=resource_group_id, updater=props.to_updater(name)
            )
        )
        return cls(ok=True, msg="success")


class DeleteScalingGroup(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        name: str,
    ) -> DeleteScalingGroup:
        graph_ctx: GraphQueryContext = info.context

        resource_group_id = await _resolve_resource_group_id(graph_ctx, name)
        await graph_ctx.processors.resource_group.purge_resource_group.run(
            PurgeResourceGroupAction(
                resource_group_id=resource_group_id,
                purger=Purger(spec=ResourceGroupNamePurgerSpec(name=name)),
            )
        )

        return cls(ok=True, msg="success")


class AssociateScalingGroupWithDomain(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_group: str,
        domain: str,
    ) -> AssociateScalingGroupWithDomain:
        graph_ctx: GraphQueryContext = info.context
        domain_data = (
            await graph_ctx.processors.domain.lookup.run(
                LookupDomainAction(name=DomainName(domain))
            )
        ).data
        resource_group_id = await _resolve_resource_group_id(graph_ctx, scaling_group)
        action = AssociateResourceGroupWithDomainsAction(
            domain_id=domain_data.id,
            binder=RBACScopeBinder(
                pairs=[
                    RBACScopeBindingPair(
                        spec=ResourceGroupForDomainCreatorSpec(
                            resource_group_id=resource_group_id,
                            domain_id=domain_data.id,
                        ),
                        entity_ref=RBACElementRef(
                            RBACElementType.RESOURCE_GROUP, str(resource_group_id)
                        ),
                        scope_ref=RBACElementRef(RBACElementType.DOMAIN, str(domain_data.id)),
                    )
                ]
            ),
        )
        await graph_ctx.processors.resource_group.associate_resource_group_with_domains.run(action)
        return cls(ok=True, msg="success")


class AssociateScalingGroupsWithDomain(graphene.Mutation):  # type: ignore[misc]
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        domain: str,
    ) -> AssociateScalingGroupsWithDomain:
        graph_ctx: GraphQueryContext = info.context
        domain_data = (
            await graph_ctx.processors.domain.lookup.run(
                LookupDomainAction(name=DomainName(domain))
            )
        ).data
        resource_group_ids = await _resolve_resource_group_ids(graph_ctx, scaling_groups)
        action = AssociateResourceGroupWithDomainsAction(
            domain_id=domain_data.id,
            binder=RBACScopeBinder(
                pairs=[
                    RBACScopeBindingPair(
                        spec=ResourceGroupForDomainCreatorSpec(
                            resource_group_id=resource_group_id,
                            domain_id=domain_data.id,
                        ),
                        entity_ref=RBACElementRef(
                            RBACElementType.RESOURCE_GROUP, str(resource_group_id)
                        ),
                        scope_ref=RBACElementRef(RBACElementType.DOMAIN, str(domain_data.id)),
                    )
                    for resource_group_id in resource_group_ids
                ]
            ),
        )
        await graph_ctx.processors.resource_group.associate_resource_group_with_domains.run(action)
        return cls(ok=True, msg="success")


class DisassociateScalingGroupWithDomain(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_group: str,
        domain: str,
    ) -> DisassociateScalingGroupWithDomain:
        graph_ctx: GraphQueryContext = info.context
        domain_data = (
            await graph_ctx.processors.domain.lookup.run(
                LookupDomainAction(name=DomainName(domain))
            )
        ).data
        resource_group_id = await _resolve_resource_group_id(graph_ctx, scaling_group)
        action = DisassociateResourceGroupWithDomainsAction(
            domain_id=domain_data.id,
            unbinder=ResourceGroupDomainEntityUnbinder(
                resource_group_ids=[resource_group_id],
                domain_id=domain_data.id,
            ),
        )
        await graph_ctx.processors.resource_group.disassociate_resource_group_with_domains.run(
            action
        )
        return cls(ok=True, msg="success")


class DisassociateScalingGroupsWithDomain(graphene.Mutation):  # type: ignore[misc]
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        domain: str,
    ) -> DisassociateScalingGroupsWithDomain:
        graph_ctx: GraphQueryContext = info.context
        domain_data = (
            await graph_ctx.processors.domain.lookup.run(
                LookupDomainAction(name=DomainName(domain))
            )
        ).data
        resource_group_ids = await _resolve_resource_group_ids(graph_ctx, scaling_groups)
        action = DisassociateResourceGroupWithDomainsAction(
            domain_id=domain_data.id,
            unbinder=ResourceGroupDomainEntityUnbinder(
                resource_group_ids=resource_group_ids,
                domain_id=domain_data.id,
            ),
        )
        await graph_ctx.processors.resource_group.disassociate_resource_group_with_domains.run(
            action
        )
        return cls(ok=True, msg="success")


class DisassociateAllScalingGroupsWithDomain(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        domain = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        domain: str,
    ) -> DisassociateAllScalingGroupsWithDomain:
        graph_ctx: GraphQueryContext = info.context
        domain_data = (
            await graph_ctx.processors.domain.lookup.run(
                LookupDomainAction(name=DomainName(domain))
            )
        ).data
        action = DisassociateResourceGroupWithDomainsAction(
            domain_id=domain_data.id,
            unbinder=ResourceGroupDomainEntityUnbinder(
                resource_group_ids=None,
                domain_id=domain_data.id,
            ),
        )
        await graph_ctx.processors.resource_group.disassociate_resource_group_with_domains.run(
            action
        )
        return cls(ok=True, msg="success")


class AssociateScalingGroupWithUserGroup(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_group: str,
        user_group: uuid.UUID,
    ) -> AssociateScalingGroupWithUserGroup:
        graph_ctx: GraphQueryContext = info.context
        resource_group_id = await _resolve_resource_group_id(graph_ctx, scaling_group)
        action = AssociateResourceGroupWithUserGroupsAction(
            project_id=ProjectID(user_group),
            binder=RBACScopeBinder(
                pairs=[
                    RBACScopeBindingPair(
                        spec=ResourceGroupForProjectCreatorSpec(
                            resource_group_id=resource_group_id,
                            project=user_group,
                        ),
                        entity_ref=RBACElementRef(
                            RBACElementType.RESOURCE_GROUP, str(resource_group_id)
                        ),
                        scope_ref=RBACElementRef(RBACElementType.PROJECT, str(user_group)),
                    )
                ]
            ),
        )
        await graph_ctx.processors.resource_group.associate_resource_group_with_user_groups.run(
            action
        )
        return cls(ok=True, msg="success")


class AssociateScalingGroupsWithUserGroup(graphene.Mutation):  # type: ignore[misc]
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        user_group: uuid.UUID,
    ) -> AssociateScalingGroupsWithUserGroup:
        graph_ctx: GraphQueryContext = info.context
        resource_group_ids = await _resolve_resource_group_ids(graph_ctx, scaling_groups)
        action = AssociateResourceGroupWithUserGroupsAction(
            project_id=ProjectID(user_group),
            binder=RBACScopeBinder(
                pairs=[
                    RBACScopeBindingPair(
                        spec=ResourceGroupForProjectCreatorSpec(
                            resource_group_id=resource_group_id,
                            project=user_group,
                        ),
                        entity_ref=RBACElementRef(
                            RBACElementType.RESOURCE_GROUP, str(resource_group_id)
                        ),
                        scope_ref=RBACElementRef(RBACElementType.PROJECT, str(user_group)),
                    )
                    for resource_group_id in resource_group_ids
                ]
            ),
        )
        await graph_ctx.processors.resource_group.associate_resource_group_with_user_groups.run(
            action
        )
        return cls(ok=True, msg="success")


class DisassociateScalingGroupWithUserGroup(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_group: str,
        user_group: uuid.UUID,
    ) -> DisassociateScalingGroupWithUserGroup:
        graph_ctx: GraphQueryContext = info.context
        resource_group_id = await _resolve_resource_group_id(graph_ctx, scaling_group)
        action = DisassociateResourceGroupWithUserGroupsAction(
            project_id=ProjectID(user_group),
            unbinder=ResourceGroupProjectEntityUnbinder(
                resource_group_ids=[resource_group_id],
                project=user_group,
            ),
        )
        await graph_ctx.processors.resource_group.disassociate_resource_group_with_user_groups.run(
            action
        )
        return cls(ok=True, msg="success")


class DisassociateScalingGroupsWithUserGroup(graphene.Mutation):  # type: ignore[misc]
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        user_group: uuid.UUID,
    ) -> DisassociateScalingGroupsWithUserGroup:
        graph_ctx: GraphQueryContext = info.context
        resource_group_ids = await _resolve_resource_group_ids(graph_ctx, scaling_groups)
        action = DisassociateResourceGroupWithUserGroupsAction(
            project_id=ProjectID(user_group),
            unbinder=ResourceGroupProjectEntityUnbinder(
                resource_group_ids=resource_group_ids,
                project=user_group,
            ),
        )
        await graph_ctx.processors.resource_group.disassociate_resource_group_with_user_groups.run(
            action
        )
        return cls(ok=True, msg="success")


class DisassociateAllScalingGroupsWithGroup(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        user_group = graphene.UUID(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        user_group: uuid.UUID,
    ) -> DisassociateAllScalingGroupsWithGroup:
        graph_ctx: GraphQueryContext = info.context
        action = DisassociateResourceGroupWithUserGroupsAction(
            project_id=ProjectID(user_group),
            unbinder=ResourceGroupProjectEntityUnbinder(
                resource_group_ids=None,
                project=user_group,
            ),
        )
        await graph_ctx.processors.resource_group.disassociate_resource_group_with_user_groups.run(
            action
        )
        return cls(ok=True, msg="success")


class AssociateScalingGroupWithKeyPair(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        access_key = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_group: str,
        access_key: str,
    ) -> AssociateScalingGroupWithKeyPair:
        graph_ctx: GraphQueryContext = info.context
        resource_group_id = await _resolve_resource_group_id(graph_ctx, scaling_group)
        action = AssociateResourceGroupWithKeypairsAction(
            resource_group_id=resource_group_id,
            bulk_creator=BulkCreator(
                specs=[
                    ResourceGroupForKeypairsCreatorSpec(
                        resource_group_id=resource_group_id,
                        access_key=AccessKey(access_key),
                    )
                ]
            ),
        )
        await graph_ctx.processors.resource_group.associate_resource_group_with_keypairs.run(action)
        return cls(ok=True, msg="success")


class AssociateScalingGroupsWithKeyPair(graphene.Mutation):  # type: ignore[misc]
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        access_key = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        access_key: str,
    ) -> AssociateScalingGroupsWithKeyPair:
        graph_ctx: GraphQueryContext = info.context
        resource_group_ids = await _resolve_resource_group_ids(graph_ctx, scaling_groups)
        action = AssociateResourceGroupWithKeypairsAction(
            resource_group_id=resource_group_ids[0],
            bulk_creator=BulkCreator(
                specs=[
                    ResourceGroupForKeypairsCreatorSpec(
                        resource_group_id=resource_group_id,
                        access_key=AccessKey(access_key),
                    )
                    for resource_group_id in resource_group_ids
                ]
            ),
        )
        await graph_ctx.processors.resource_group.associate_resource_group_with_keypairs.run(action)
        return cls(ok=True, msg="success")


class DisassociateScalingGroupWithKeyPair(graphene.Mutation):  # type: ignore[misc]
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_group = graphene.String(required=True)
        access_key = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_group: str,
        access_key: str,
    ) -> DisassociateScalingGroupWithKeyPair:
        graph_ctx: GraphQueryContext = info.context
        resource_group_id = await _resolve_resource_group_id(graph_ctx, scaling_group)
        action = DisassociateResourceGroupWithKeypairsAction(
            resource_group_id=resource_group_id,
            purger=create_resource_group_for_keypairs_purger(
                resource_group_id=resource_group_id,
                access_key=AccessKey(access_key),
            ),
        )
        await graph_ctx.processors.resource_group.disassociate_resource_group_with_keypairs.run(
            action
        )
        return cls(ok=True, msg="success")


class DisassociateScalingGroupsWithKeyPair(graphene.Mutation):  # type: ignore[misc]
    """Added in 24.03.9."""

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        scaling_groups = graphene.List(graphene.String, required=True)
        access_key = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @classmethod
    async def mutate(
        cls,
        root: Any,
        info: graphene.ResolveInfo,
        scaling_groups: Sequence[str],
        access_key: str,
    ) -> DisassociateScalingGroupsWithKeyPair:
        graph_ctx: GraphQueryContext = info.context
        resource_group_id = await _resolve_resource_group_id(graph_ctx, scaling_groups[0])
        action = DisassociateResourceGroupWithKeypairsAction(
            resource_group_id=resource_group_id,
            purger=create_resource_group_for_keypairs_purger(
                resource_group_id=resource_group_id,
                access_key=AccessKey(access_key),
            ),
        )
        await graph_ctx.processors.resource_group.disassociate_resource_group_with_keypairs.run(
            action
        )
        return cls(ok=True, msg="success")
