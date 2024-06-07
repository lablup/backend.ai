import logging
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Sequence

import graphene
import sqlalchemy as sa
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.logging_utils import BraceStyleAdapter

from ..api.exceptions import RoutingNotFound
from .base import GUID, Base, EnumValueType, IDColumn, InferenceSessionError, Item, PaginatedList

if TYPE_CHECKING:
    # from .gql import GraphQueryContext
    from .endpoint import EndpointRow


__all__ = ("RoutingRow", "Routing", "RoutingList", "RouteStatus")


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class RouteStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TERMINATING = "terminating"
    PROVISIONING = "provisioning"
    FAILED_TO_START = "failed_to_start"


class RoutingRow(Base):
    __tablename__ = "routings"
    __table_args__ = (
        sa.UniqueConstraint("endpoint", "session", name="uq_routings_endpoint_session"),
    )

    id = IDColumn("id")
    endpoint = sa.Column(
        "endpoint", GUID, sa.ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=False
    )
    session = sa.Column(
        "session", GUID, sa.ForeignKey("sessions.id", ondelete="RESTRICT"), nullable=True
    )
    session_owner = sa.Column(
        "session_owner", GUID, sa.ForeignKey("users.uuid", ondelete="RESTRICT"), nullable=False
    )
    domain = sa.Column(
        "domain",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="RESTRICT"),
        nullable=False,
    )
    project = sa.Column(
        "project",
        GUID,
        sa.ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status = sa.Column(
        "status",
        EnumValueType(RouteStatus),
        nullable=False,
        default=RouteStatus.PROVISIONING,
    )

    traffic_ratio = sa.Column("traffic_ratio", sa.Float(), nullable=False)
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=True,
    )

    error_data = sa.Column("error_data", pgsql.JSONB(), nullable=True, default=sa.null())

    endpoint_row = relationship("EndpointRow", back_populates="routings")
    session_row = relationship("SessionRow", back_populates="routing")

    @classmethod
    async def get_by_session(
        cls,
        db_sess: AsyncSession,
        session_id: uuid.UUID,
        load_endpoint=False,
        project: Optional[uuid.UUID] = None,
        domain: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> "RoutingRow":
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        query = sa.select(RoutingRow).where(RoutingRow.session == session_id)
        if load_endpoint:
            query = query.options(selectinload(RoutingRow.endpoint_row))
        if project:
            query = query.filter(RoutingRow.project == project)
        if domain:
            query = query.filter(RoutingRow.domain == domain)
        if user_uuid:
            query = query.filter(RoutingRow.session_owner == user_uuid)
        result = await db_sess.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    @classmethod
    async def list(
        cls,
        db_sess: AsyncSession,
        endpoint_id: uuid.UUID,
        load_endpoint=False,
        status_filter: list[RouteStatus] = [
            RouteStatus.HEALTHY,
            RouteStatus.UNHEALTHY,
            RouteStatus.PROVISIONING,
        ],
        project: Optional[uuid.UUID] = None,
        domain: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> list["RoutingRow"]:
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        query = (
            sa.select(RoutingRow)
            .filter(RoutingRow.endpoint == endpoint_id)
            .filter(RoutingRow.status.in_(status_filter))
            .order_by(sa.desc(RoutingRow.created_at))
        )
        if load_endpoint:
            query = query.options(selectinload(RoutingRow.endpoint_row))
        if project:
            query = query.filter(RoutingRow.project == project)
        if domain:
            query = query.filter(RoutingRow.domain == domain)
        if user_uuid:
            query = query.filter(RoutingRow.session_owner == user_uuid)
        result = await db_sess.execute(query)
        rows = result.scalars().all()
        return rows

    @classmethod
    async def get(
        cls,
        db_sess: AsyncSession,
        route_id: uuid.UUID,
        load_session=False,
        load_endpoint=False,
        project: Optional[uuid.UUID] = None,
        domain: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> "RoutingRow":
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        query = sa.select(RoutingRow).where(RoutingRow.id == route_id)
        if load_session:
            query = query.options(selectinload(RoutingRow.session_row))
        if load_endpoint:
            query = query.options(selectinload(RoutingRow.endpoint_row))
        if project:
            query = query.filter(RoutingRow.project == project)
        if domain:
            query = query.filter(RoutingRow.domain == domain)
        if user_uuid:
            query = query.filter(RoutingRow.session_owner == user_uuid)
        result = await db_sess.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    def __init__(
        self,
        id: uuid.UUID,
        endpoint: uuid.UUID,
        session: uuid.UUID | None,
        session_owner: uuid.UUID,
        domain: str,
        project: uuid.UUID,
        status=RouteStatus.PROVISIONING,
        traffic_ratio=1.0,
    ) -> None:
        self.id = id
        self.endpoint = endpoint
        self.session = session
        self.session_owner = session_owner
        self.domain = domain
        self.project = project
        self.status = status
        self.traffic_ratio = traffic_ratio


class Routing(graphene.ObjectType):
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

    @classmethod
    async def from_row(
        cls,
        ctx,  # ctx: GraphQueryContext,
        row: RoutingRow,
        endpoint: Optional["EndpointRow"] = None,
    ) -> "Routing":
        return cls(
            routing_id=row.id,
            endpoint=(endpoint or row.endpoint_row).url,
            session=row.session,
            status=row.status.name,
            traffic_ratio=row.traffic_ratio,
            created_at=row.created_at,
            error_data=row.error_data,
        )

    @classmethod
    async def load_count(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        endpoint_id: Optional[uuid.UUID] = None,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from()
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
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx,  # ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        endpoint_id: Optional[uuid.UUID] = None,
        filter: str | None = None,
        order: str | None = None,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> Sequence["Routing"]:
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
            return [await cls.from_row(ctx, row) async for row in (await session.stream(query))]

    @classmethod
    async def load_all(
        cls,
        ctx,  # ctx: GraphQueryContext
        endpoint_id: uuid.UUID,
        *,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> Sequence["Routing"]:
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
        ctx,  # ctx: GraphQueryContext,
        *,
        routing_id: uuid.UUID,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> "Routing":
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await RoutingRow.get(
                    session, routing_id, project=project, domain=domain_name, user_uuid=user_uuid
                )
        except NoResultFound:
            raise RoutingNotFound
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


class RoutingList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Routing, required=True)
