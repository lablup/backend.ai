from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    EnumValueType,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
    from ai.backend.manager.models.endpoint import EndpointRow
    from ai.backend.manager.models.session import SessionRow


__all__ = ("RouteStatus", "RoutingRow")


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


def _get_deployment_revision_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow

    return RoutingRow.revision == DeploymentRevisionRow.id


class RoutingRow(Base):  # type: ignore[misc]
    __tablename__ = "routings"
    __table_args__ = (
        sa.UniqueConstraint("endpoint", "session", name="uq_routings_endpoint_session"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    endpoint: Mapped[uuid.UUID] = mapped_column(
        "endpoint", GUID, sa.ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=False
    )
    session: Mapped[uuid.UUID | None] = mapped_column(
        "session", GUID, sa.ForeignKey("sessions.id", ondelete="RESTRICT"), nullable=True
    )
    session_owner: Mapped[uuid.UUID] = mapped_column(
        "session_owner", GUID, sa.ForeignKey("users.uuid", ondelete="RESTRICT"), nullable=False
    )
    domain: Mapped[str] = mapped_column(
        "domain",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="RESTRICT"),
        nullable=False,
    )
    project: Mapped[uuid.UUID] = mapped_column(
        "project",
        GUID,
        sa.ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[RouteStatus] = mapped_column(
        "status",
        EnumValueType(RouteStatus),
        nullable=False,
        default=RouteStatus.PROVISIONING,
    )
    weight: Mapped[int | None] = mapped_column("weight", sa.Integer(), nullable=True, default=None)
    traffic_ratio: Mapped[float] = mapped_column("traffic_ratio", sa.Float(), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=True,
    )

    error_data: Mapped[dict | None] = mapped_column(
        "error_data", pgsql.JSONB(), nullable=True, default=sa.null()
    )

    # Revision reference without FK (relationship only)
    revision: Mapped[uuid.UUID | None] = mapped_column("revision", GUID, nullable=True)
    traffic_status: Mapped[RouteTrafficStatus] = mapped_column(
        "traffic_status",
        EnumValueType(RouteTrafficStatus),
        nullable=False,
        server_default=sa.text("'active'"),
        default=RouteTrafficStatus.ACTIVE,
    )

    endpoint_row: Mapped[EndpointRow] = relationship("EndpointRow", back_populates="routings")
    session_row: Mapped[SessionRow | None] = relationship("SessionRow", back_populates="routing")
    revision_row: Mapped[DeploymentRevisionRow | None] = relationship(
        "DeploymentRevisionRow",
        primaryjoin=_get_deployment_revision_join_condition,
        foreign_keys="RoutingRow.revision",
        viewonly=True,
    )

    @classmethod
    async def get_by_session(
        cls,
        db_sess: AsyncSession,
        session_id: uuid.UUID,
        load_endpoint: bool = False,
        project: uuid.UUID | None = None,
        domain: str | None = None,
        user_uuid: uuid.UUID | None = None,
    ) -> RoutingRow:
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
        load_endpoint: bool = False,
        load_session: bool = False,
        status_filter: list[RouteStatus] | None = None,
        project: uuid.UUID | None = None,
        domain: str | None = None,
        user_uuid: uuid.UUID | None = None,
    ) -> Sequence[RoutingRow]:
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        if status_filter is None:
            status_filter = list(RouteStatus.active_route_statuses())
        query = (
            sa.select(RoutingRow)
            .filter(RoutingRow.endpoint == endpoint_id)
            .filter(RoutingRow.status.in_(status_filter))
            .order_by(sa.desc(RoutingRow.created_at))
        )
        if load_endpoint:
            query = query.options(selectinload(RoutingRow.endpoint_row))
        if load_session:
            query = query.options(selectinload(RoutingRow.session_row))
        if project:
            query = query.filter(RoutingRow.project == project)
        if domain:
            query = query.filter(RoutingRow.domain == domain)
        if user_uuid:
            query = query.filter(RoutingRow.session_owner == user_uuid)
        result = await db_sess.execute(query)
        return result.scalars().all()

    @classmethod
    async def get(
        cls,
        db_sess: AsyncSession,
        route_id: uuid.UUID,
        load_session: bool = False,
        load_endpoint: bool = False,
        project: uuid.UUID | None = None,
        domain: str | None = None,
        user_uuid: uuid.UUID | None = None,
    ) -> RoutingRow:
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
        status: RouteStatus = RouteStatus.PROVISIONING,
        traffic_ratio: float = 1.0,
        revision: uuid.UUID | None = None,
        traffic_status: RouteTrafficStatus = RouteTrafficStatus.ACTIVE,
    ) -> None:
        self.id = id
        self.endpoint = endpoint
        self.session = session
        self.session_owner = session_owner
        self.domain = domain
        self.project = project
        self.status = status
        self.traffic_ratio = traffic_ratio
        self.revision = revision
        self.traffic_status = traffic_status

    def delegate_ownership(self, user_uuid: uuid.UUID) -> None:
        self.session_owner = user_uuid

    def to_data(self) -> RoutingData:
        return RoutingData(
            id=self.id,
            endpoint=self.endpoint,
            session=self.session,
            status=self.status,
            traffic_ratio=self.traffic_ratio,
            created_at=self.created_at,
            error_data=self.error_data or {},
        )

    def to_route_info(self) -> RouteInfo:
        return RouteInfo(
            route_id=self.id,
            endpoint_id=self.endpoint,
            session_id=SessionId(self.session) if self.session else None,
            status=self.status,
            traffic_ratio=self.traffic_ratio,
            created_at=self.created_at,
            revision_id=self.revision,
            traffic_status=self.traffic_status,
            error_data=self.error_data or {},
        )
