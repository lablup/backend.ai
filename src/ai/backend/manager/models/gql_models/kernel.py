from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Mapping,
    Optional,
    Self,
    Type,
    TypeVar,
    cast,
)

import graphene
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import noload, selectinload

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    BinarySize,
    KernelId,
    SessionId,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.base import (
    Item,
    PaginatedList,
    batch_multiresult,
    batch_multiresult_in_scalar_stream,
    batch_result,
)
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.minilang import JSONFieldItem
from ai.backend.manager.models.minilang.ordering import ColumnMapType, QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import (
    FieldSpecType,
    QueryFilterParser,
)

from ...defs import DEFAULT_ROLE
from ..gql_relay import AsyncNode, Connection
from ..kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    DEFAULT_KERNEL_ORDERING,
    LIVE_STATUS,
    KernelRow,
    kernels,
)
from ..user import UserRole, users
from .base import (
    BigInt,
)
from .image import ImageNode

if TYPE_CHECKING:
    from ..gql import GraphQueryContext

__all__ = (
    "KernelNode",
    "KernelConnection",
    "ComputeContainer",
    "ComputeContainerList",
    "LegacyComputeSession",
    "LegacyComputeSessionList",
)


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
    image_reference = graphene.String(description="Added in 25.4.0.")
    architecture = graphene.String(
        description="Added in 25.4.0. The architecture that the image of this kernel requires"
    )

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
    async def batch_load_by_session_id(
        cls,
        graph_ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Sequence[Self]]:
        async with graph_ctx.db.begin_readonly_session() as db_sess:
            query = sa.select(KernelRow).where(KernelRow.session_id.in_(session_ids))
            return await batch_multiresult_in_scalar_stream(
                graph_ctx,
                db_sess,
                query,
                cls,
                session_ids,
                lambda row: row.session_id,
            )

    @classmethod
    async def batch_load_by_agent_id(
        cls,
        graph_ctx: GraphQueryContext,
        agent_ids: Sequence[AgentId],
    ) -> Sequence[Sequence[Self]]:
        async with graph_ctx.db.begin_readonly_session() as db_sess:
            query = sa.select(KernelRow).where(KernelRow.agent.in_(agent_ids))
            return await batch_multiresult_in_scalar_stream(
                graph_ctx,
                db_sess,
                query,
                cls,
                agent_ids,
                lambda row: row.agent,
            )

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: KernelRow) -> Self:
        # TODO: Replace 'hide-agents' option to RBAC
        is_superadmin = ctx.user["role"] == UserRole.SUPERADMIN
        if is_superadmin:
            hide_agents = False
        else:
            hide_agents = ctx.config_provider.config.manager.hide_agents
        status_history = row.status_history or {}
        return KernelNode(
            id=row.id,  # auto-converted to Relay global ID
            row_id=row.id,
            cluster_idx=row.cluster_idx,
            cluster_hostname=row.cluster_hostname,
            local_rank=row.local_rank,
            cluster_role=row.cluster_role,
            session_id=row.session_id,
            architecture=row.architecture,
            image_reference=row.image,
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

    async def resolve_image(self, info: graphene.ResolveInfo) -> Optional[ImageNode]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader_by_func(
            graph_ctx, ImageNode.batch_load_by_name_and_arch
        )
        images = cast(list[ImageNode], await loader.load((self.image_reference, self.architecture)))
        try:
            return images[0]
        except IndexError:
            return None

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
        kernel_ids_str = [str(kid) for kid in kernel_ids]
        return await ctx.valkey_stat.get_session_statistics_batch(kernel_ids_str)


class KernelConnection(Connection):
    class Meta:
        node = KernelNode
        description = "Added in 24.09.0."


class ComputeContainer(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    # identity
    idx = graphene.Int()  # legacy
    role = graphene.String()  # legacy
    hostname = graphene.String()  # legacy
    kernel_id = graphene.UUID(description="Added in 24.03.1.")
    cluster_idx = graphene.Int()
    local_rank = graphene.Int()
    cluster_role = graphene.String()
    cluster_hostname = graphene.String()
    session_id = graphene.UUID()  # owner session

    # image
    image = graphene.String(description="Deprecated since 24.03.0; use image_object.name")
    image_object = graphene.Field(ImageNode, description="Added in 24.03.0.")
    architecture = graphene.String()
    registry = graphene.String()

    # status
    status = graphene.String()
    status_changed = GQLDateTime()
    status_info = graphene.String()
    status_data = graphene.JSONString()
    created_at = GQLDateTime()
    terminated_at = GQLDateTime()
    starts_at = GQLDateTime()
    scheduled_at = GQLDateTime()
    abusing_report = graphene.JSONString()

    # resources
    agent = graphene.String()
    agent_addr = graphene.String()
    container_id = graphene.String()
    resource_opts = graphene.JSONString()
    occupied_slots = graphene.JSONString()
    live_stat = graphene.JSONString()
    last_stat = graphene.JSONString()
    preopen_ports = graphene.List(lambda: graphene.Int, required=False)

    @classmethod
    def parse_row(cls, ctx: GraphQueryContext, row: KernelRow) -> Mapping[str, Any]:
        assert row is not None
        from .user import UserRole

        is_superadmin = ctx.user["role"] == UserRole.SUPERADMIN
        if is_superadmin:
            hide_agents = False
        else:
            hide_agents = ctx.config_provider.config.manager.hide_agents
        status_history = row.status_history or {}
        return {
            # identity
            "id": row.id,
            "kernel_id": row.id,
            "idx": row.cluster_idx,
            "role": row.cluster_role,
            "hostname": row.cluster_hostname,
            "cluster_idx": row.cluster_idx,
            "local_rank": row.local_rank,
            "cluster_role": row.cluster_role,
            "cluster_hostname": row.cluster_hostname,
            "session_id": row.session_id,
            # image
            "image": row.image,
            "image_object": ImageNode.from_row(ctx, row.image_row),
            "architecture": row.architecture,
            "registry": row.registry,
            # status
            "status": row.status.name,
            "status_changed": row.status_changed,
            "status_info": row.status_info,
            "status_data": row.status_data,
            "created_at": row.created_at,
            "terminated_at": row.terminated_at,
            "starts_at": row.starts_at,
            "scheduled_at": status_history.get(KernelStatus.SCHEDULED.name),
            "occupied_slots": row.occupied_slots.to_json(),
            # resources
            "agent": row.agent if not hide_agents else None,
            "agent_addr": row.agent_addr if not hide_agents else None,
            "container_id": row.container_id if not hide_agents else None,
            "resource_opts": row.resource_opts,
            "preopen_ports": row.preopen_ports,
            # statistics
            # last_stat is resolved by Graphene (resolve_last_stat method)
        }

    @classmethod
    def from_row(cls, ctx: GraphQueryContext, row: Row) -> Optional[ComputeContainer]:
        if row is None:
            return None
        props = cls.parse_row(ctx, row)
        return cls(**props)

    # last_stat also fetches data from Redis, meaning that
    # both live_stat and last_stat will reference same data from same source
    # we can leave last_stat value for legacy support, as an alias to last_stat
    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "KernelStatistics.by_kernel")
        return await loader.load(self.id)

    async def resolve_last_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        return await self.resolve_live_stat(info)

    async def resolve_abusing_report(
        self,
        info: graphene.ResolveInfo,
        access_key: AccessKey | None,
    ) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        if access_key is None:
            return None
        return await graph_ctx.registry.get_abusing_report(self.id)

    _queryfilter_fieldspec: FieldSpecType = {
        "image": ("image", None),
        "architecture": ("architecture", None),
        "agent": ("agent", None),
        "agent_addr": ("agent_addr", None),
        "cluster_idx": ("cluster_idx", None),
        "local_rank": ("local_rank", None),
        "cluster_role": ("cluster_role", None),
        "cluster_hostname": ("cluster_hostname", None),
        "status": ("status", KernelStatus),
        "status_info": ("status_info", None),
        "created_at": ("created_at", dtparse),
        "status_changed": ("status_changed", dtparse),
        "terminated_at": ("terminated_at", dtparse),
        "scheduled_at": (JSONFieldItem("status_history", KernelStatus.SCHEDULED.name), dtparse),
    }

    _queryorder_colmap: ColumnMapType = {
        "image": ("image", None),
        "architecture": ("architecture", None),
        "agent": ("agent", None),
        "agent_addr": ("agent_addr", None),
        "cluster_idx": ("cluster_idx", None),
        "local_rank": ("local_rank", None),
        "cluster_role": ("cluster_role", None),
        "cluster_hostname": ("cluster_hostname", None),
        "status": ("status", None),
        "status_info": ("status_info", None),
        "status_changed": ("status_changed", None),
        "created_at": ("created_at", None),
        "terminated_at": ("terminated_at", None),
        "scheduled_at": (JSONFieldItem("status_history", KernelStatus.SCHEDULED.name), None),
    }

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        session_id: SessionId,
        *,
        cluster_role: Optional[str] = None,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        access_key: Optional[str] = None,
        filter: Optional[str] = None,
    ) -> int:
        query = (
            sa.select([sa.func.count()])
            .select_from(KernelRow)
            .where(KernelRow.session_id == session_id)
        )
        if cluster_role is not None:
            query = query.where(KernelRow.cluster_role == cluster_role)
        if domain_name is not None:
            query = query.where(KernelRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(KernelRow.group_id == group_id)
        if access_key is not None:
            query = query.where(KernelRow.access_key == access_key)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        async with ctx.db.begin_readonly_session() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        session_id: SessionId,
        *,
        cluster_role: Optional[str] = None,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        access_key: Optional[AccessKey] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence[Optional[ComputeContainer]]:
        query = (
            sa.select(KernelRow)
            .where(KernelRow.session_id == session_id)
            .limit(limit)
            .offset(offset)
            .options(selectinload(KernelRow.image_row).options(selectinload(ImageRow.aliases)))
        )
        if cluster_role is not None:
            query = query.where(KernelRow.cluster_role == cluster_role)
        if domain_name is not None:
            query = query.where(KernelRow.domain_name == domain_name)
        if group_id is not None:
            query = query.where(KernelRow.group_id == group_id)
        if access_key is not None:
            query = query.where(KernelRow.access_key == access_key)
        if filter is not None:
            qfparser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = qfparser.append_filter(query, filter)
        if order is not None:
            qoparser = QueryOrderParser(cls._queryorder_colmap)
            query = qoparser.append_ordering(query, order)
        else:
            query = query.order_by(*DEFAULT_KERNEL_ORDERING)
        async with ctx.db.begin_readonly_session() as db_session:
            return [cls.from_row(ctx, r) async for r in (await db_session.stream_scalars(query))]

    @classmethod
    async def batch_load_by_session(
        cls,
        ctx: GraphQueryContext,
        session_ids: Sequence[SessionId],
    ) -> Sequence[Sequence[ComputeContainer]]:
        query = (
            sa.select(KernelRow)
            # TODO: use "owner session ID" when we implement multi-container session
            .where(KernelRow.session_id.in_(session_ids))
            .options(selectinload(KernelRow.image_row).options(selectinload(ImageRow.aliases)))
        )
        async with ctx.db.begin_readonly_session() as conn:
            return await batch_multiresult(
                ctx,
                conn,
                query,
                cls,
                session_ids,
                lambda row: row.session_id,
            )

    @classmethod
    async def batch_load_by_agent_id(
        cls,
        ctx: GraphQueryContext,
        agent_ids: Sequence[AgentId],
        *,
        status: Optional[KernelStatus] = None,
    ) -> Sequence[Sequence[ComputeContainer]]:
        query_stmt = (
            sa.select(KernelRow)
            .where(KernelRow.agent.in_(agent_ids))
            .options(selectinload(KernelRow.image_row).options(selectinload(ImageRow.aliases)))
        )
        kernel_status: tuple[KernelStatus, ...]
        if status is not None:
            kernel_status = (status,)
        else:
            kernel_status = AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES
        query_stmt = query_stmt.where(KernelRow.status.in_(kernel_status))
        async with ctx.db.begin_readonly_session() as db_session:
            return await batch_multiresult_in_scalar_stream(
                ctx,
                db_session,
                query_stmt,
                cls,
                agent_ids,
                lambda row: row.agent,
            )

    @classmethod
    async def batch_load_detail(
        cls,
        ctx: GraphQueryContext,
        container_ids: Sequence[KernelId],
        *,
        domain_name: Optional[str] = None,
        access_key: Optional[AccessKey] = None,
    ) -> Sequence[Optional[ComputeContainer]]:
        query = (
            sa.select(KernelRow)
            .where(
                (KernelRow.id.in_(container_ids)),
            )
            .options(
                noload("*"),
                selectinload(KernelRow.group_row),
                selectinload(KernelRow.user_row),
                selectinload(KernelRow.image_row),
            )
        )
        if domain_name is not None:
            query = query.where(KernelRow.domain_name == domain_name)
        if access_key is not None:
            query = query.where(KernelRow.access_key == access_key)
        async with ctx.db.begin_readonly_session() as conn:
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                container_ids,
                lambda row: row.id,
            )


class ComputeContainerList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(ComputeContainer, required=True)


# --------- pre-v5 legacy -----------

MetricValueType = TypeVar("MetricValueType", int, float)


class LegacyComputeSession(graphene.ObjectType):
    """
    Represents a main session.
    """

    class Meta:
        interfaces = (Item,)

    tag = graphene.String()  # Only for ComputeSession
    sess_id = graphene.String()  # legacy
    sess_type = graphene.String()  # legacy
    session_name = graphene.String()
    session_type = graphene.String()
    role = graphene.String()
    image = graphene.String()
    architecture = graphene.String()
    registry = graphene.String()
    domain_name = graphene.String()
    group_name = graphene.String()
    group_id = graphene.UUID()
    scaling_group = graphene.String()
    user_uuid = graphene.UUID()
    access_key = graphene.String()

    status = graphene.String()
    status_changed = GQLDateTime()
    status_info = graphene.String()
    created_at = GQLDateTime()
    terminated_at = GQLDateTime()
    startup_command = graphene.String()
    result = graphene.String()

    # hidable fields by configuration
    agent = graphene.String()
    container_id = graphene.String()

    service_ports = graphene.JSONString()

    occupied_slots = graphene.JSONString()
    occupied_shares = graphene.JSONString()
    mounts = graphene.List(lambda: graphene.List(lambda: graphene.String))
    resource_opts = graphene.JSONString()

    num_queries = BigInt()
    live_stat = graphene.JSONString()
    last_stat = graphene.JSONString()

    user_email = graphene.String()

    # Legacy fields
    lang = graphene.String()
    mem_slot = graphene.Int()
    cpu_slot = graphene.Float()
    gpu_slot = graphene.Float()
    tpu_slot = graphene.Float()
    cpu_used = BigInt()
    cpu_using = graphene.Float()
    mem_max_bytes = BigInt()
    mem_cur_bytes = BigInt()
    net_rx_bytes = BigInt()
    net_tx_bytes = BigInt()
    io_read_bytes = BigInt()
    io_write_bytes = BigInt()
    io_max_scratch_size = BigInt()
    io_cur_scratch_size = BigInt()

    # last_stat also fetches data from Redis, meaning that
    # both live_stat and last_stat will reference same data from same source
    # we can leave last_stat value for legacy support, as an alias to last_stat
    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "KernelStatistics.by_kernel")
        return await loader.load(self.id)

    async def resolve_last_stat(self, info: graphene.ResolveInfo) -> Optional[Mapping[str, Any]]:
        return await self.resolve_live_stat(info)

    async def _resolve_legacy_metric(
        self,
        info: graphene.ResolveInfo,
        metric_key: str,
        metric_field: str,
        convert_type: Type[MetricValueType],
    ) -> Optional[MetricValueType]:
        if not hasattr(self, "status"):
            return None
        graph_ctx: GraphQueryContext = info.context
        if KernelStatus[self.status] not in LIVE_STATUS:
            if self.last_stat is None:
                return convert_type(0)
            metric = self.last_stat.get(metric_key)
            if metric is None:
                return convert_type(0)
            value = metric.get(metric_field)
            if value is None:
                return convert_type(0)
            return convert_type(value)
        else:
            loader = graph_ctx.dataloader_manager.get_loader(
                graph_ctx, "KernelStatistics.by_kernel"
            )
            kstat = await loader.load(self.id)
            if kstat is None:
                return convert_type(0)
            metric = kstat.get(metric_key)
            if metric is None:
                return convert_type(0)
            value = metric.get(metric_field)
            if value is None:
                return convert_type(0)
            return convert_type(value)

    async def resolve_cpu_used(self, info: graphene.ResolveInfo) -> Optional[float]:
        return await self._resolve_legacy_metric(info, "cpu_used", "current", float)

    async def resolve_cpu_using(self, info: graphene.ResolveInfo) -> Optional[float]:
        return await self._resolve_legacy_metric(info, "cpu_util", "pct", float)

    async def resolve_mem_max_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "mem", "stats.max", int)

    async def resolve_mem_cur_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "mem", "current", int)

    async def resolve_net_rx_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "net_rx", "stats.rate", int)

    async def resolve_net_tx_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "net_tx", "stats.rate", int)

    async def resolve_io_read_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "io_read", "current", int)

    async def resolve_io_write_bytes(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "io_write", "current", int)

    async def resolve_io_max_scratch_size(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "io_scratch_size", "stats.max", int)

    async def resolve_io_cur_scratch_size(self, info: graphene.ResolveInfo) -> Optional[int]:
        return await self._resolve_legacy_metric(info, "io_scratch_size", "current", int)

    @classmethod
    def parse_row(cls, ctx: GraphQueryContext, row: Row) -> Mapping[str, Any]:
        assert row is not None
        from .user import UserRole

        mega = 2**20
        is_superadmin = ctx.user["role"] == UserRole.SUPERADMIN
        if is_superadmin:
            hide_agents = False
        else:
            hide_agents = ctx.config_provider.config.manager.hide_agents
        return {
            "id": row["id"],
            "sess_id": row["session_name"],  # legacy, will be deprecated
            "sess_type": row["session_type"].name,  # legacy, will be deprecated
            "session_name": row["session_name"],
            "session_type": row["session_type"].name,
            "role": row["cluster_role"],
            "tag": row["tag"],
            "image": row["image"],
            "architecture": row["architecture"],
            "registry": row["registry"],
            "domain_name": row["domain_name"],
            "group_name": row[
                "name"
            ],  # group.name (group is omitted since use_labels=True is not used)
            "group_id": row["group_id"],
            "scaling_group": row["scaling_group"],
            "user_uuid": row["user_uuid"],
            "access_key": row["access_key"],
            "status": row["status"].name,
            "status_changed": row["status_changed"],
            "status_info": row["status_info"],
            "created_at": row["created_at"],
            "terminated_at": row["terminated_at"],
            "startup_command": row["startup_command"],
            "result": row["result"].name,
            "service_ports": row["service_ports"],
            "occupied_slots": row["occupied_slots"].to_json(),
            "resource_opts": row["resource_opts"],
            "num_queries": row["num_queries"],
            # optionally hidden
            "agent": row["agent"] if not hide_agents else None,
            "container_id": row["container_id"] if not hide_agents else None,
            # live_stat is resolved by Graphene
            # last_stat is resolved by Graphene
            "user_email": row["email"],
            # Legacy fields
            # NOTE: currently graphene always uses resolve methods!
            "cpu_used": 0,
            "mem_max_bytes": 0,
            "mem_cur_bytes": 0,
            "net_rx_bytes": 0,
            "net_tx_bytes": 0,
            "io_read_bytes": 0,
            "io_write_bytes": 0,
            "io_max_scratch_size": 0,
            "io_cur_scratch_size": 0,
            "lang": row["image"],
            "occupied_shares": row["occupied_shares"],
            "mem_slot": BinarySize.from_str(row["occupied_slots"].get("mem", 0)) // mega,
            "cpu_slot": float(row["occupied_slots"].get("cpu", 0)),
            "gpu_slot": float(row["occupied_slots"].get("cuda.device", 0)),
            "tpu_slot": float(row["occupied_slots"].get("tpu.device", 0)),
        }

    @classmethod
    def from_row(cls, context: GraphQueryContext, row: Row) -> Optional[LegacyComputeSession]:
        if row is None:
            return None
        props = cls.parse_row(context, row)
        return cls(**props)

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        access_key: Optional[AccessKey] = None,
        status: Optional[str] = None,
    ) -> int:
        if isinstance(status, str):
            status_list = [KernelStatus[s] for s in status.split(",")]
        elif isinstance(status, KernelStatus):
            status_list = [status]
        query = (
            sa.select([sa.func.count()])
            .select_from(kernels)
            .where(kernels.c.cluster_role == DEFAULT_ROLE)
        )
        if domain_name is not None:
            query = query.where(kernels.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(kernels.c.group_id == group_id)
        if access_key is not None:
            query = query.where(kernels.c.access_key == access_key)
        if status is not None:
            query = query.where(kernels.c.status.in_(status_list))
        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        access_key: Optional[AccessKey] = None,
        status: Optional[str] = None,
        order_key: Optional[str] = None,
        order_asc: bool = True,
    ) -> Sequence[LegacyComputeSession]:
        if isinstance(status, str):
            status_list = [KernelStatus[s] for s in status.split(",")]
        elif isinstance(status, KernelStatus):
            status_list = [status]
        if order_key is None:
            _ordering = DEFAULT_KERNEL_ORDERING
        else:
            _order_func = sa.asc if order_asc else sa.desc
            _ordering = [_order_func(getattr(kernels.c, order_key))]
        j = kernels.join(groups, groups.c.id == kernels.c.group_id).join(
            users, users.c.uuid == kernels.c.user_uuid
        )
        query = (
            sa.select([kernels, groups.c.name, users.c.email])
            .select_from(j)
            .where(kernels.c.cluster_role == DEFAULT_ROLE)
            .order_by(*_ordering)
            .limit(limit)
            .offset(offset)
        )
        if domain_name is not None:
            query = query.where(kernels.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(kernels.c.group_id == group_id)
        if access_key is not None:
            query = query.where(kernels.c.access_key == access_key)
        if status is not None:
            query = query.where(kernels.c.status.in_(status_list))
        async with ctx.db.begin_readonly() as conn:
            return [
                obj
                async for r in (await conn.stream(query))
                if (obj := cls.from_row(ctx, r)) is not None
            ]

    @classmethod
    async def batch_load(
        cls,
        ctx: GraphQueryContext,
        access_keys: AccessKey,
        *,
        domain_name: Optional[str] = None,
        group_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> Sequence[Optional[LegacyComputeSession]]:
        j = kernels.join(groups, groups.c.id == kernels.c.group_id).join(
            users, users.c.uuid == kernels.c.user_uuid
        )
        query = (
            sa.select([kernels, groups.c.name, users.c.email])
            .select_from(j)
            .where(
                (kernels.c.access_key.in_(access_keys)) & (kernels.c.cluster_role == DEFAULT_ROLE),
            )
            .order_by(
                sa.desc(
                    sa.func.greatest(
                        kernels.c.created_at,
                        kernels.c.terminated_at,
                        kernels.c.status_changed,
                    )
                ),
            )
            .limit(100)
        )
        if domain_name is not None:
            query = query.where(kernels.c.domain_name == domain_name)
        if group_id is not None:
            query = query.where(kernels.c.group_id == group_id)
        if status is not None:
            query = query.where(kernels.c.status == status)
        async with ctx.db.begin_readonly() as conn:
            return await batch_result(
                ctx,
                conn,
                query,
                cls,
                access_keys,
                lambda row: row["access_key"],
            )

    @classmethod
    async def batch_load_detail(
        cls,
        ctx: GraphQueryContext,
        sess_ids: Sequence[SessionId],
        *,
        domain_name: Optional[str] = None,
        access_key: Optional[AccessKey] = None,
        status: Optional[str] = None,
    ) -> Sequence[Sequence[LegacyComputeSession]]:
        status_list = []
        if isinstance(status, str):
            status_list = [KernelStatus[s] for s in status.split(",")]
        elif isinstance(status, KernelStatus):
            status_list = [status]
        elif status is None:
            status_list = [KernelStatus["RUNNING"]]
        j = kernels.join(groups, groups.c.id == kernels.c.group_id).join(
            users, users.c.uuid == kernels.c.user_uuid
        )
        query = (
            sa.select([kernels, groups.c.name, users.c.email])
            .select_from(j)
            .where((kernels.c.cluster_role == DEFAULT_ROLE) & (kernels.c.session_id.in_(sess_ids)))
        )
        if domain_name is not None:
            query = query.where(kernels.c.domain_name == domain_name)
        if access_key is not None:
            query = query.where(kernels.c.access_key == access_key)
        if status_list:
            query = query.where(kernels.c.status.in_(status_list))
        async with ctx.db.begin_readonly() as conn:
            return await batch_multiresult(
                ctx,
                conn,
                query,
                cls,
                sess_ids,
                lambda row: row["session_id"],
            )


class LegacyComputeSessionList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(LegacyComputeSession, required=True)
