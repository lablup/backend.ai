from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Self
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from sqlalchemy.sql.dml import Delete, Update
from sqlalchemy.sql.selectable import Select

from ai.backend.common.types import ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    ResourceSlotColumn,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.scaling_group import ScalingGroupRow

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.models"))

__all__: Sequence[str] = ("resource_presets",)


# Type alias for statements that support .where() method
type WhereableStatement[T] = Select[T] | Update | Delete


def filter_by_name(name: str) -> Callable[[WhereableStatement[Any]], WhereableStatement[Any]]:
    return lambda query_stmt: query_stmt.where(ResourcePresetRow.name == name)


def filter_by_id(id: UUID) -> Callable[[WhereableStatement[Any]], WhereableStatement[Any]]:
    return lambda query_stmt: query_stmt.where(ResourcePresetRow.id == id)


# QueryOption is a function that takes a statement and returns a filtered statement
type QueryOption = Callable[[WhereableStatement[Any]], WhereableStatement[Any]]


def _get_scaling_group_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.scaling_group import ScalingGroupRow

    return ScalingGroupRow.name == foreign(ResourcePresetRow.scaling_group_name)


class ResourcePresetRow(Base):
    __tablename__ = "resource_presets"
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=256), nullable=False)
    resource_slots: Mapped[ResourceSlot] = mapped_column(
        "resource_slots", ResourceSlotColumn(), nullable=False
    )
    shared_memory: Mapped[int | None] = mapped_column(
        "shared_memory", sa.BigInteger(), nullable=True
    )

    # If `scaling_group_name` is None, the preset is global
    scaling_group_name: Mapped[str | None] = mapped_column(
        "scaling_group_name", sa.String(length=64), nullable=True, server_default=sa.null()
    )
    scaling_group_row: Mapped[ScalingGroupRow | None] = relationship(
        "ScalingGroupRow",
        back_populates="resource_preset_rows",
        primaryjoin=_get_scaling_group_join_condition,
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
    async def update(
        cls,
        query_option: QueryOption,
        data: Mapping[str, Any],
        *,
        db_session: AsyncSession,
    ) -> Self | None:
        base_update_stmt = sa.update(ResourcePresetRow).values(data).returning(ResourcePresetRow)
        filtered_stmt = query_option(base_update_stmt)
        stmt = (
            sa.select(ResourcePresetRow)
            .from_statement(filtered_stmt)
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
        base_delete_stmt = sa.delete(ResourcePresetRow)
        filtered_stmt = query_option(base_delete_stmt)
        await db_session.execute(filtered_stmt)

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
