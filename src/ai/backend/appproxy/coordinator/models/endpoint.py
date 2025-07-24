from datetime import datetime
from typing import TYPE_CHECKING, Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from ai.backend.appproxy.common.exceptions import ObjectNotFound
from ai.backend.appproxy.common.types import HealthCheckConfig

from .base import (
    Base,
    IDColumn,
    StructuredJSONObjectColumn,
)

if TYPE_CHECKING:
    from .circuit import Circuit


__all__ = [
    "Endpoint",
]


class Endpoint(Base):
    __tablename__ = "endpoints"

    """
    Store model service endpoint information and health check configuration
    """

    id: Mapped[UUID] = IDColumn()

    health_check_enabled: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, default=False)
    health_check_config: Mapped[HealthCheckConfig | None] = mapped_column(
        StructuredJSONObjectColumn(HealthCheckConfig), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    circuit_row: Mapped["Circuit"] = relationship(
        back_populates="endpoint_row",
        primaryjoin="Circuit.endpoint_id == Endpoint.id",
        foreign_keys="Circuit.endpoint_id",
    )

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        endpoint_id: UUID,
        *,
        load_circuit: bool = False,
    ) -> "Endpoint":
        query = sa.select(Endpoint).where((Endpoint.id == endpoint_id))
        if load_circuit:
            query = query.options(selectinload(Endpoint.circuit_row))
        endpoint = await session.scalar(query)
        if not endpoint:
            raise ObjectNotFound(object_name="endpoint")
        return endpoint

    @classmethod
    async def list_endpoints(
        cls,
        session: AsyncSession,
    ) -> Sequence["Endpoint"]:
        query = sa.select(Endpoint)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def list_health_check_enabled(
        cls,
        session: AsyncSession,
    ) -> Sequence["Endpoint"]:
        query = sa.select(Endpoint).where(Endpoint.health_check_enabled.is_(True))
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    def create(
        cls,
        endpoint_id: UUID,
        health_check_enabled: bool = False,
        health_check_config: HealthCheckConfig | None = None,
    ) -> "Endpoint":
        endpoint = cls()
        endpoint.id = endpoint_id
        endpoint.health_check_enabled = health_check_enabled
        endpoint.health_check_config = health_check_config
        return endpoint
