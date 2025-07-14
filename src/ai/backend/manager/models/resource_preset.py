from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Callable, Optional, Self
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.services.resource_preset.types import (
    ResourcePresetCreator,
)

from .base import (
    Base,
    IDColumn,
    ResourceSlotColumn,
)

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models"))

__all__: Sequence[str] = ("resource_presets",)


type QueryStatement = sa.sql.Select


def filter_by_name(name: str) -> Callable[[QueryStatement], QueryStatement]:
    return lambda query_stmt: query_stmt.where(ResourcePresetRow.name == name)


def filter_by_id(id: UUID) -> Callable[[QueryStatement], QueryStatement]:
    return lambda query_stmt: query_stmt.where(ResourcePresetRow.id == id)


QueryOption = Callable[[Any], Callable[[QueryStatement], QueryStatement]]


class ResourcePresetRow(Base):
    __tablename__ = "resource_presets"
    id = IDColumn()
    name = sa.Column("name", sa.String(length=256), nullable=False)
    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    shared_memory = sa.Column("shared_memory", sa.BigInteger(), nullable=True)

    # If `scaling_group_name` is None, the preset is global
    scaling_group_name = sa.Column(
        "scaling_group_name", sa.String(length=64), nullable=True, server_default=sa.null()
    )
    scaling_group_row = relationship(
        "ScalingGroupRow",
        back_populates="resource_preset_rows",
        primaryjoin="ScalingGroupRow.name == foreign(ResourcePresetRow.scaling_group_name)",
    )

    __table_args__ = (
        sa.Index(
            "ix_resource_presets_name_null_scaling_group_name",
            name,
            postgresql_where=scaling_group_name.is_(None),
            unique=True,
        ),
        sa.Index(
            "ix_resource_presets_name_scaling_group_name",
            name,
            scaling_group_name,
            postgresql_where=scaling_group_name.isnot(None),
            unique=True,
        ),
    )

    @classmethod
    async def create(
        cls,
        creator: ResourcePresetCreator,
        *,
        db_session: AsyncSession,
    ) -> Optional[Self]:
        to_store = creator.fields_to_store()
        insert_stmt = sa.insert(ResourcePresetRow).values(to_store).returning(ResourcePresetRow)
        stmt = sa.select(ResourcePresetRow).from_statement(insert_stmt)

        try:
            return await db_session.scalar(stmt)
        except sa.exc.IntegrityError:
            # A resource preset with the given name and scaling group name already exists
            return None

    @classmethod
    async def update(
        cls,
        query_option: QueryOption,
        data: Mapping[str, Any],
        *,
        db_session: AsyncSession,
    ) -> Optional[Self]:
        update_stmt = sa.update(ResourcePresetRow).values(data).returning(ResourcePresetRow)
        update_stmt = query_option(update_stmt)
        stmt = (
            sa.select(ResourcePresetRow)
            .from_statement(update_stmt)
            .execution_options(populate_existing=True)
        )
        try:
            return await db_session.scalar(stmt)
        except sa.exc.IntegrityError:
            return None

    @classmethod
    async def delete(
        cls,
        query_option: QueryOption,
        *,
        db_session: AsyncSession,
    ) -> None:
        delete_stmt = sa.delete(ResourcePresetRow)
        delete_stmt = query_option(delete_stmt)
        return await db_session.execute(delete_stmt)

    def to_dataclass(self) -> ResourcePresetData:
        return ResourcePresetData(
            id=self.id,
            name=self.name,
            resource_slots=self.resource_slots,
            shared_memory=self.shared_memory,
            scaling_group_name=self.scaling_group_name,
        )


# For compatibility
resource_presets = ResourcePresetRow.__table__
