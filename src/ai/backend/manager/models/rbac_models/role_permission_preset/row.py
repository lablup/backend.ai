from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)


class RolePermissionPresetRow(Base):  # type: ignore[misc]
    __tablename__ = "role_permission_presets"
    __table_args__ = (
        sa.UniqueConstraint(
            "role_preset_id",
            "entity_type",
            "operation",
            name="uq_role_permission_presets_preset_entity_op",
        ),
    )

    id: Mapped[RolePermissionPresetID] = mapped_column(
        "id",
        GUID(RolePermissionPresetID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    role_preset_id: Mapped[RolePresetID] = mapped_column(
        "role_preset_id",
        GUID(RolePresetID),
        sa.ForeignKey("role_presets.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    operation: Mapped[OperationType] = mapped_column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
