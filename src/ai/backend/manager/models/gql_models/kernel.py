from __future__ import annotations

from collections.abc import Sequence
from typing import (
    TYPE_CHECKING,
    Any,
)

import graphene
from graphene.types.datetime import DateTime as GQLDateTime
from redis.asyncio import Redis

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.types import KernelId

from ..gql_relay import AsyncNode, Connection
from ..image import ImageNode
from ..kernel import KernelRow, KernelStatus
from ..user import UserRole

if TYPE_CHECKING:
    from ..gql import GraphQueryContext


class KernelNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)
        description = "Added in 24.09.0."

    # identity
    row_id = graphene.UUID(description="ID of kernel.")
    cluster_idx = graphene.Int()
    local_rank = graphene.Int()
    cluster_role = graphene.String()
    cluster_hostname = graphene.String()
    session_id = graphene.UUID()

    # image
    image = graphene.Field(ImageNode)

    # status
    status = graphene.String()
    status_changed = GQLDateTime()
    status_info = graphene.String()
    status_data = graphene.JSONString()
    created_at = GQLDateTime()
    terminated_at = GQLDateTime()
    starts_at = GQLDateTime()
    scheduled_at = GQLDateTime()

    # resources
    agent_id = graphene.String()
    agent_addr = graphene.String()
    container_id = graphene.String()
    resource_opts = graphene.JSONString()
    occupied_slots = graphene.JSONString()
    live_stat = graphene.JSONString()
    abusing_report = graphene.JSONString()
    preopen_ports = graphene.List(lambda: graphene.Int)

    @classmethod
    def from_row(cls, info: graphene.ResolveInfo, row: KernelRow) -> KernelNode:
        ctx: GraphQueryContext = info.context

        # TODO: Replace 'hide-agents' option to RBAC
        is_superadmin = ctx.user["role"] == UserRole.SUPERADMIN
        if is_superadmin:
            hide_agents = False
        else:
            hide_agents = ctx.local_config["manager"]["hide-agents"]
        status_history = row.status_history or {}
        return KernelNode(
            id=row.id,
            row_id=row.id,
            cluster_idx=row.cluster_idx,
            cluster_hostname=row.cluster_hostname,
            local_rank=row.local_rank,
            cluster_role=row.cluster_role,
            session_id=row.session_id,
            status=row.status,
            status_changed=row.status_changed,
            status_info=row.status_info,
            status_data=row.status_data,
            created_at=row.created_at,
            terminated_at=row.terminated_at,
            starts_at=row.starts_at,
            scheduled_at=status_history.get(KernelStatus.SCHEDULED.name),
            occupied_slots=row.occupied_slots.to_json(),
            agent_id=row.agent if not hide_agents else None,
            agent_addr=row.agent_addr if not hide_agents else None,
            container_id=row.container_id if not hide_agents else None,
            resource_opts=row.resource_opts,
            preopen_ports=row.preopen_ports,
        )

    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> dict[str, Any] | None:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader_by_func(
            graph_ctx, self.batch_load_live_stat
        )
        return await loader.load(self.row_id)

    @classmethod
    async def batch_load_live_stat(
        cls, ctx: GraphQueryContext, kernel_ids: Sequence[KernelId]
    ) -> list[dict[str, Any] | None]:
        async def _pipe_builder(r: Redis):
            pipe = r.pipeline()
            for kid in kernel_ids:
                await pipe.get(str(kid))
            return pipe

        ret: list[dict[str, Any] | None] = []
        for stat in await redis_helper.execute(ctx.redis_stat, _pipe_builder):
            if stat is not None:
                ret.append(msgpack.unpackb(stat))
            else:
                ret.append(None)

        return ret


class KernelConnection(Connection):
    class Meta:
        node = KernelNode
        description = "Added in 24.09.0."
