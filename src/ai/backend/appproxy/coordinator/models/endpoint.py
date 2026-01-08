from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

from ai.backend.appproxy.common.errors import ObjectNotFound
from ai.backend.common.config import ModelHealthCheck

from .base import (
    GUID,
    Base,
    BaseMixin,
    StructuredJSONObjectColumn,
)

if TYPE_CHECKING:
    pass


__all__ = [
    "Endpoint",
]


class Endpoint(Base, BaseMixin):
    __tablename__ = "endpoints"

    """
    Store model service endpoint information and health check configuration
    """

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    health_check_enabled: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, default=False)
    health_check_config: Mapped[ModelHealthCheck | None] = mapped_column(
        StructuredJSONObjectColumn(ModelHealthCheck), nullable=True
    )

    created_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    circuit_row = relationship(
        "Circuit",
        back_populates="endpoint_row",
        primaryjoin="Circuit.endpoint_id == Endpoint.id",
        foreign_keys="Circuit.endpoint_id",
        uselist=False,
    )

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        endpoint_id: UUID,
        *,
        load_circuit: bool = False,
    ) -> "Endpoint":
        query = sa.select(Endpoint).where(Endpoint.id == endpoint_id)
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
        health_check_config: ModelHealthCheck | None = None,
    ) -> "Endpoint":
        endpoint = cls()
        endpoint.id = endpoint_id
        endpoint.health_check_enabled = health_check_enabled
        endpoint.health_check_config = health_check_config
        return endpoint
