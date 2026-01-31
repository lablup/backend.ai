from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    cast,
)

import graphene
import graphene_federation
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from graphql import Undefined
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import load_only

from ai.backend.common.types import AccessKey, AgentId, ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupOpts,
    ScalingGroupRow,
    scaling_groups,
    sgroups_for_domains,
    sgroups_for_groups,
    sgroups_for_keypairs,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base.creator import BulkCreator, Creator
from ai.backend.manager.repositories.base.purger import BatchPurger, Purger
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.scaling_group.creators import (
    ScalingGroupCreatorSpec,
    ScalingGroupForDomainCreatorSpec,
    ScalingGroupForKeypairsCreatorSpec,
    ScalingGroupForProjectCreatorSpec,
)
from ai.backend.manager.repositories.scaling_group.purgers import (
    AllScalingGroupsForDomainPurgerSpec,
    AllScalingGroupsForProjectPurgerSpec,
    ScalingGroupForDomainPurgerSpec,
    ScalingGroupForKeypairsPurgerSpec,
    ScalingGroupForProjectPurgerSpec,
    ScalingGroupsForDomainPurgerSpec,
    ScalingGroupsForKeypairsPurgerSpec,
    ScalingGroupsForProjectPurgerSpec,
)
from ai.backend.manager.repositories.scaling_group.updaters import (
    ScalingGroupDriverConfigUpdaterSpec,
    ScalingGroupMetadataUpdaterSpec,
    ScalingGroupNetworkConfigUpdaterSpec,
    ScalingGroupSchedulerConfigUpdaterSpec,
    ScalingGroupStatusUpdaterSpec,
    ScalingGroupUpdaterSpec,
)
from ai.backend.manager.services.scaling_group.actions.associate_with_domain import (
    AssociateScalingGroupWithDomainsAction,
)
from ai.backend.manager.services.scaling_group.actions.associate_with_keypair import (
    AssociateScalingGroupWithKeypairsAction,
)
from ai.backend.manager.services.scaling_group.actions.associate_with_user_group import (
    AssociateScalingGroupWithUserGroupsAction,
)
from ai.backend.manager.services.scaling_group.actions.create import (
    CreateScalingGroupAction,
)
from ai.backend.manager.services.scaling_group.actions.disassociate_with_domain import (
    DisassociateScalingGroupWithDomainsAction,
)
from ai.backend.manager.services.scaling_group.actions.disassociate_with_keypair import (
    DisassociateScalingGroupWithKeypairsAction,
)
from ai.backend.manager.services.scaling_group.actions.disassociate_with_user_group import (
    DisassociateScalingGroupWithUserGroupsAction,
)
from ai.backend.manager.services.scaling_group.actions.modify import (
    ModifyScalingGroupAction,
)
from ai.backend.manager.services.scaling_group.actions.purge_scaling_group import (
    PurgeScalingGroupAction,
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
        row: ScalingGroupRow,
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
    async def __resolve_reference(self, info: graphene.ResolveInfo, **kwargs: Any) -> ScalingGroupNode:
        _, scaling_group_name = AsyncNode.resolve_global_id(info, self.id)
        graph_ctx: GraphQueryContext = info.context
        async with graph_ctx.db.begin_readonly_session() as db_session:
            query_stmt = sa.select(ScalingGroupRow).where(
                ScalingGroupRow.name == scaling_group_name
            )
            result = await db_session.scalar(query_stmt)
            if result is None:
                raise ScalingGroupNotFound(f"Scaling group not found: {scaling_group_name}")
            return ScalingGroupNode.from_row(graph_ctx, result)

    @classmethod
    async def batch_load_by_group(
        cls,
        ctx: GraphQueryContext,
        group_ids: Sequence[uuid.UUID],
    ) -> Sequence[Sequence[ScalingGroupNode]]:
        j = sa.join(
            ScalingGroupRow,
            ScalingGroupForProjectRow,
            ScalingGroupRow.name == ScalingGroupForProjectRow.scaling_group,
        )
        _stmt = (
            sa.select(ScalingGroupRow)
            .select_from(j)
            .where(ScalingGroupForProjectRow.group.in_(group_ids))
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
            ScalingGroupRow,
            ScalingGroupForDomainRow,
            ScalingGroupRow.name == ScalingGroupForDomainRow.scaling_group,
        )
        _stmt = (
            sa.select(ScalingGroupRow)
            .select_from(j)
            .where(ScalingGroupForDomainRow.domain.in_(domain_names))
        )
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
            ScalingGroupRow,
            ScalingGroupForKeypairsRow,
            ScalingGroupRow.name == ScalingGroupForKeypairsRow.scaling_group,
        )
        _stmt = (
            sa.select(ScalingGroupRow)
            .select_from(j)
            .where(ScalingGroupForKeypairsRow.access_key.in_(access_keys))
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


class ScalingGroupConnection(Connection):  # type: ignore[misc]
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

        graph_ctx = info.context
        async with graph_ctx.db.begin_readonly_session() as db_session:
            query_stmt = (
                sa.select(AgentRow)
                .where(
                    (AgentRow.scaling_group == self.name) & (AgentRow.status == AgentStatus[status])
                )
                .options(load_only(AgentRow.available_slots))
            )
            result = (await db_session.scalars(query_stmt)).all()
            agent_rows = cast(list[AgentRow], result)

            total_occupied_slots = ResourceSlot()
            total_available_slots = ResourceSlot()

            known_slot_types = (
                await graph_ctx.config_provider.legacy_etcd_config_loader.get_resource_slots()
            )
            for agent_row in agent_rows:
                occupied_slots = await agent_row.get_occupied_slots(
                    graph_ctx.db, AgentId(agent_row.id), known_slot_types
                )
                total_occupied_slots += occupied_slots
                total_available_slots += agent_row.available_slots

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
        return dict(result.to_json()) if result is not None else {}

    # TODO: Replace this field with a generic resource slot query API
    async def resolve_own_session_occupied_resource_slots(
        self, info: graphene.ResolveInfo
    ) -> Mapping[str, Any]:
        from ai.backend.manager.models.agent.row import AgentRow
        from ai.backend.manager.models.kernel import (
            AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
            KernelRow,
        )

        graph_ctx: GraphQueryContext = info.context
        user = graph_ctx.user
        async with graph_ctx.db.begin_readonly_session() as db_session:
            query = (
                sa.select(KernelRow)
                .join(KernelRow.agent_row)
                .where(
                    sa.and_(
                        KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES),
                        KernelRow.user_uuid == user["uuid"],
                        AgentRow.scaling_group == self.name,
                    )
                )
            )
            result = await db_session.scalars(query)
        kernel_rows = cast(list[KernelRow], result.all())
        occupied_slots = ResourceSlot()
        for kernel in kernel_rows:
            occupied_slots += kernel.occupied_slots
        return occupied_slots.to_json()

    async def resolve_accelerator_quantum_size(self, info: graphene.ResolveInfo) -> float | None:
        graph_ctx: GraphQueryContext = info.context
        result = await graph_ctx.etcd.get("config/plugins/accelerator/cuda/quantum_size")
        return float(result) if result is not None else None

    @classmethod
    def from_row(
        cls,
        ctx: GraphQueryContext,
        row: Row | None,
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
            scheduler_opts=row.scheduler_opts.to_json(),
            use_host_network=row.use_host_network,
        )

    @classmethod
    def from_orm_row(
        cls,
        row: ScalingGroupRow,
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
            scheduler_opts=row.scheduler_opts.to_json(),
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
        query = sa.select(scaling_groups).select_from(scaling_groups)
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
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
            scaling_groups,
            sgroups_for_domains,
            scaling_groups.c.name == sgroups_for_domains.c.scaling_group,
        )
        query = (
            sa.select(scaling_groups).select_from(j).where(sgroups_for_domains.c.domain == domain)
        )
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
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
            scaling_groups,
            sgroups_for_groups,
            scaling_groups.c.name == sgroups_for_groups.c.scaling_group,
        )
        query = sa.select(scaling_groups).select_from(j).where(sgroups_for_groups.c.group == group)
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
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
            scaling_groups,
            sgroups_for_keypairs,
            scaling_groups.c.name == sgroups_for_keypairs.c.scaling_group,
        )
        query = (
            sa.select(scaling_groups)
            .select_from(j)
            .where(sgroups_for_keypairs.c.access_key == access_key)
        )
        if is_active is not None:
            query = query.where(scaling_groups.c.is_active == is_active)
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
            scaling_groups,
            sgroups_for_groups,
            scaling_groups.c.name == sgroups_for_groups.c.scaling_group,
        )
        query = (
            sa.select(scaling_groups, sgroups_for_groups.c.group)
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
            sa.select(scaling_groups)
            .select_from(scaling_groups)
            .where(scaling_groups.c.name.in_(names))
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

    def to_updater(self, name: str) -> Updater[ScalingGroupRow]:
        """Convert GraphQL input to Updater for scaling group modification."""
        status_spec = ScalingGroupStatusUpdaterSpec(
            is_active=OptionalState.from_graphql(self.is_active),
            is_public=OptionalState.from_graphql(self.is_public),
        )
        metadata_spec = ScalingGroupMetadataUpdaterSpec(
            description=TriState.from_graphql(self.description),
        )
        network_spec = ScalingGroupNetworkConfigUpdaterSpec(
            wsproxy_addr=TriState.from_graphql(self.wsproxy_addr),
            wsproxy_api_token=TriState.from_graphql(self.wsproxy_api_token),
            use_host_network=OptionalState.from_graphql(self.use_host_network),
        )
        driver_spec = ScalingGroupDriverConfigUpdaterSpec(
            driver=OptionalState.from_graphql(self.driver),
            driver_opts=OptionalState.from_graphql(self.driver_opts),
        )
        scheduler_spec = ScalingGroupSchedulerConfigUpdaterSpec(
            scheduler=OptionalState.from_graphql(self.scheduler),
            scheduler_opts=OptionalState.from_graphql(
                ScalingGroupOpts.from_json(self.scheduler_opts)
                if self.scheduler_opts is not None and self.scheduler_opts is not Undefined
                else Undefined
            ),
        )
        spec = ScalingGroupUpdaterSpec(
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
        spec = ScalingGroupCreatorSpec(
            name=name,
            description=props.description,
            is_active=bool(props.is_active),
            is_public=bool(props.is_public),
            wsproxy_addr=props.wsproxy_addr,
            wsproxy_api_token=props.wsproxy_api_token,
            driver=props.driver,
            driver_opts=props.driver_opts,
            scheduler=props.scheduler,
            scheduler_opts=ScalingGroupOpts.from_json(props.scheduler_opts),
            use_host_network=bool(props.use_host_network),
        )
        creator = Creator(spec=spec)
        action = CreateScalingGroupAction(creator=creator)
        result = await graph_ctx.processors.scaling_group.create_scaling_group.wait_for_complete(
            action
        )
        return cls(
            ok=True,
            msg="success",
            scaling_group=ScalingGroup(
                name=result.scaling_group.name,
                description=result.scaling_group.metadata.description,
                is_active=result.scaling_group.status.is_active,
                is_public=result.scaling_group.status.is_public,
                created_at=result.scaling_group.metadata.created_at,
                wsproxy_addr=result.scaling_group.network.wsproxy_addr,
                wsproxy_api_token=result.scaling_group.network.wsproxy_api_token,
                driver=result.scaling_group.driver.name,
                driver_opts=dict(result.scaling_group.driver.options),
                scheduler=result.scaling_group.scheduler.name.value,
                scheduler_opts=result.scaling_group.scheduler.options.to_json(),
                use_host_network=result.scaling_group.network.use_host_network,
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
        await graph_ctx.processors.scaling_group.modify_scaling_group.wait_for_complete(
            ModifyScalingGroupAction(updater=props.to_updater(name))
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

        await graph_ctx.processors.scaling_group.purge_scaling_group.wait_for_complete(
            PurgeScalingGroupAction(purger=Purger(row_class=ScalingGroupRow, pk_value=name))
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
        action = AssociateScalingGroupWithDomainsAction(
            bulk_creator=BulkCreator(
                specs=[
                    ScalingGroupForDomainCreatorSpec(
                        scaling_group=scaling_group,
                        domain=domain,
                    )
                ]
            )
        )
        await graph_ctx.processors.scaling_group.associate_scaling_group_with_domains.wait_for_complete(
            action
        )
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
        action = AssociateScalingGroupWithDomainsAction(
            bulk_creator=BulkCreator(
                specs=[
                    ScalingGroupForDomainCreatorSpec(
                        scaling_group=scaling_group,
                        domain=domain,
                    )
                    for scaling_group in scaling_groups
                ]
            )
        )
        await graph_ctx.processors.scaling_group.associate_scaling_group_with_domains.wait_for_complete(
            action
        )
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
        action = DisassociateScalingGroupWithDomainsAction(
            purger=BatchPurger(
                spec=ScalingGroupForDomainPurgerSpec(
                    scaling_group=scaling_group,
                    domain=domain,
                ),
            )
        )
        await graph_ctx.processors.scaling_group.disassociate_scaling_group_with_domains.wait_for_complete(
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
        action = DisassociateScalingGroupWithDomainsAction(
            purger=BatchPurger(
                spec=ScalingGroupsForDomainPurgerSpec(
                    scaling_groups=list(scaling_groups),
                    domain=domain,
                ),
            )
        )
        await graph_ctx.processors.scaling_group.disassociate_scaling_group_with_domains.wait_for_complete(
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
        action = DisassociateScalingGroupWithDomainsAction(
            purger=BatchPurger(
                spec=AllScalingGroupsForDomainPurgerSpec(
                    domain=domain,
                ),
            )
        )
        await graph_ctx.processors.scaling_group.disassociate_scaling_group_with_domains.wait_for_complete(
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
        action = AssociateScalingGroupWithUserGroupsAction(
            bulk_creator=BulkCreator(
                specs=[
                    ScalingGroupForProjectCreatorSpec(
                        scaling_group=scaling_group,
                        project=user_group,
                    )
                ]
            )
        )
        await graph_ctx.processors.scaling_group.associate_scaling_group_with_user_groups.wait_for_complete(
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
        action = AssociateScalingGroupWithUserGroupsAction(
            bulk_creator=BulkCreator(
                specs=[
                    ScalingGroupForProjectCreatorSpec(
                        scaling_group=scaling_group,
                        project=user_group,
                    )
                    for scaling_group in scaling_groups
                ]
            )
        )
        await graph_ctx.processors.scaling_group.associate_scaling_group_with_user_groups.wait_for_complete(
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
        action = DisassociateScalingGroupWithUserGroupsAction(
            purger=BatchPurger(
                spec=ScalingGroupForProjectPurgerSpec(
                    scaling_group=scaling_group,
                    project=user_group,
                ),
            )
        )
        await graph_ctx.processors.scaling_group.disassociate_scaling_group_with_user_groups.wait_for_complete(
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
        action = DisassociateScalingGroupWithUserGroupsAction(
            purger=BatchPurger(
                spec=ScalingGroupsForProjectPurgerSpec(
                    scaling_groups=list(scaling_groups),
                    project=user_group,
                ),
            )
        )
        await graph_ctx.processors.scaling_group.disassociate_scaling_group_with_user_groups.wait_for_complete(
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
        action = DisassociateScalingGroupWithUserGroupsAction(
            purger=BatchPurger(
                spec=AllScalingGroupsForProjectPurgerSpec(
                    project=user_group,
                ),
            )
        )
        await graph_ctx.processors.scaling_group.disassociate_scaling_group_with_user_groups.wait_for_complete(
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
        action = AssociateScalingGroupWithKeypairsAction(
            bulk_creator=BulkCreator(
                specs=[
                    ScalingGroupForKeypairsCreatorSpec(
                        scaling_group=scaling_group,
                        access_key=AccessKey(access_key),
                    )
                ]
            )
        )
        await graph_ctx.processors.scaling_group.associate_scaling_group_with_keypairs.wait_for_complete(
            action
        )
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
        action = AssociateScalingGroupWithKeypairsAction(
            bulk_creator=BulkCreator(
                specs=[
                    ScalingGroupForKeypairsCreatorSpec(
                        scaling_group=scaling_group,
                        access_key=AccessKey(access_key),
                    )
                    for scaling_group in scaling_groups
                ]
            )
        )
        await graph_ctx.processors.scaling_group.associate_scaling_group_with_keypairs.wait_for_complete(
            action
        )
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
        action = DisassociateScalingGroupWithKeypairsAction(
            purger=BatchPurger(
                spec=ScalingGroupForKeypairsPurgerSpec(
                    scaling_group=scaling_group,
                    access_key=AccessKey(access_key),
                ),
            )
        )
        await graph_ctx.processors.scaling_group.disassociate_scaling_group_with_keypairs.wait_for_complete(
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
        action = DisassociateScalingGroupWithKeypairsAction(
            purger=BatchPurger(
                spec=ScalingGroupsForKeypairsPurgerSpec(
                    scaling_groups=list(scaling_groups),
                    access_key=AccessKey(access_key),
                ),
            )
        )
        await graph_ctx.processors.scaling_group.disassociate_scaling_group_with_keypairs.wait_for_complete(
            action
        )
        return cls(ok=True, msg="success")
