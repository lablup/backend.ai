from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Self, cast

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.exc import NoResultFound

from ai.backend.manager.data.deployment.types import RouteStatus
from ai.backend.manager.errors.service import RoutingNotFound
from ai.backend.manager.models.routing import RoutingRow

from .base import InferenceSessionError, Item, PaginatedList

if TYPE_CHECKING:
    from ai.backend.manager.models.endpoint import EndpointRow

    from .schema import GraphQueryContext

__all__ = ("Routing", "RoutingList")


class Routing(graphene.ObjectType):  # type: ignore[misc]
    class Meta:
        interfaces = (Item,)

    routing_id = graphene.UUID()
    endpoint = graphene.String()
    session = graphene.UUID()
    status = graphene.String()
    traffic_ratio = graphene.Float()
    created_at = GQLDateTime()
    error = InferenceSessionError()
    error_data = graphene.JSONString()

    live_stat = graphene.JSONString(description="Added in 24.12.0.")

    _endpoint_row: EndpointRow

    @classmethod
    def from_dto(cls, dto: Any) -> Self | None:
        if dto is None:
            return None
        return cls(
            routing_id=dto.id,
            endpoint=dto.endpoint,
            session=dto.session,
            status=dto.status.name,
            traffic_ratio=dto.traffic_ratio,
            created_at=dto.created_at,
            error_data=dto.error_data,
        )

    @classmethod
    async def from_row(
        cls,
        ctx: GraphQueryContext,
        row: RoutingRow,
        endpoint: EndpointRow | None = None,
    ) -> Routing:
        ret = cls(
            routing_id=row.id,
            endpoint=(endpoint or row.endpoint_row).url,
            session=row.session,
            status=row.status.name,
            traffic_ratio=row.traffic_ratio,
            created_at=row.created_at,
            error_data=row.error_data,
        )
        ret._endpoint_row = endpoint or row.endpoint_row
        return ret

    @classmethod
    async def load_count(
        cls,
        ctx: GraphQueryContext,
        *,
        endpoint_id: uuid.UUID | None = None,
        project: uuid.UUID | None = None,
        domain_name: str | None = None,
        user_uuid: uuid.UUID | None = None,
    ) -> int:
        query = sa.select(sa.func.count()).select_from()
        if endpoint_id is not None:
            query = query.where(RoutingRow.endpoint == endpoint_id)
        if project:
            query = query.filter(RoutingRow.project == project)
        if domain_name:
            query = query.filter(RoutingRow.domain == domain_name)
        if user_uuid:
            query = query.filter(RoutingRow.session_owner == user_uuid)
        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar() or 0

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        endpoint_id: uuid.UUID | None = None,
        filter: str | None = None,
        order: str | None = None,
        project: uuid.UUID | None = None,
        domain_name: str | None = None,
        user_uuid: uuid.UUID | None = None,
    ) -> Sequence[Routing]:
        query = (
            sa.select(RoutingRow)
            .limit(limit)
            .offset(offset)
            .order_by(sa.desc(RoutingRow.created_at))
        )

        if endpoint_id is not None:
            query = query.where(RoutingRow.endpoint == endpoint_id)
        if project:
            query = query.filter(RoutingRow.project == project)
        if domain_name:
            query = query.filter(RoutingRow.domain == domain_name)
        if user_uuid:
            query = query.filter(RoutingRow.session_owner == user_uuid)
        """
        if filter is not None:
            parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = parser.append_filter(query, filter)
        if order is not None:
            parser = QueryOrderParser(cls._queryorder_colmap)
            query = parser.append_ordering(query, order)
        """
        async with ctx.db.begin_readonly_session() as session:
            return [
                await cls.from_row(ctx, row) async for row in (await session.stream_scalars(query))
            ]

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        endpoint_id: uuid.UUID,
        *,
        project: uuid.UUID | None = None,
        domain_name: str | None = None,
        user_uuid: uuid.UUID | None = None,
    ) -> Sequence[Routing]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await RoutingRow.list(
                session,
                endpoint_id,
                project=project,
                domain=domain_name,
                user_uuid=user_uuid,
            )
        return [await Routing.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx: GraphQueryContext,
        *,
        routing_id: uuid.UUID,
        project: uuid.UUID | None = None,
        domain_name: str | None = None,
        user_uuid: uuid.UUID | None = None,
    ) -> Routing:
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await RoutingRow.get(
                    session, routing_id, project=project, domain=domain_name, user_uuid=user_uuid
                )
        except NoResultFound as e:
            raise RoutingNotFound from e
        return await Routing.from_row(ctx, row)

    async def resolve_error(self, info: graphene.ResolveInfo) -> Any:
        if self.status != RouteStatus.FAILED_TO_START or not self.error_data:
            return None
        match self.error_data["type"]:
            case "session_cancelled":
                session_id = self.error_data["session_id"]
            case _:
                session_id = None
        return InferenceSessionError(
            session_id=session_id,
            errors=[
                InferenceSessionError.InferenceSessionErrorInfo(
                    src=e["src"], name=e["name"], repr=e["repr"]
                )
                for e in self.error_data["errors"]
            ],
        )

    async def resolve_live_stat(self, info: graphene.ResolveInfo) -> Mapping[str, Any] | None:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader(graph_ctx, "EndpointStatistics.by_replica")
        return cast(
            Mapping[str, Any] | None, await loader.load((self._endpoint_row.id, self.routing_id))
        )


class RoutingList(graphene.ObjectType):  # type: ignore[misc]
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Routing, required=True)
