from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Self

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.manager.data.permission.permission import PermissionCreator, PermissionData
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

if TYPE_CHECKING:
    from .permission_group import PermissionGroupRow


def _get_permission_group_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.rbac_models.permission.permission_group import (
        PermissionGroupRow,
    )

    return PermissionGroupRow.id == foreign(PermissionRow.permission_group_id)


class PermissionRow(Base):  # type: ignore[misc]
    __tablename__ = "permissions"
    __table_args__ = (sa.Index("ix_id_permission_group_id", "id", "permission_group_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    permission_group_id: Mapped[uuid.UUID] = mapped_column(
        "permission_group_id",
        GUID,
        sa.ForeignKey("permission_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    operation: Mapped[OperationType] = mapped_column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )

    permission_group_row: Mapped[PermissionGroupRow | None] = relationship(
        "PermissionGroupRow",
        back_populates="permission_rows",
        primaryjoin=_get_permission_group_join_condition,
    )

    @classmethod
    def from_input(cls, input: PermissionCreator) -> Self:
        return cls(
            permission_group_id=input.permission_group_id,
            entity_type=input.entity_type,
            operation=input.operation,
        )

    def to_data(self) -> PermissionData:
        return PermissionData(
            id=self.id,
            permission_group_id=self.permission_group_id,
            entity_type=self.entity_type,
            operation=self.operation,
        )
