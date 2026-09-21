from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.base import (
    GUID,
    Base,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin


class RolePresetRow(LifecycleTimestampsMixin, Base):
    __tablename__ = "role_presets"
    __table_args__ = (
        sa.Index(
            "ix_role_presets_scope_type_deleted",
            "scope_type",
            "deleted",
        ),
    )

    id: Mapped[RolePresetID] = mapped_column(
        "id", GUID(RolePresetID), primary_key=True, server_default=sa.text("uuid_generate_v7()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(64), nullable=False)
    role_name_template: Mapped[str | None] = mapped_column(
        "role_name_template", sa.Text, nullable=True
    )
    scope_type: Mapped[EntityType] = mapped_column(
        "scope_type", sa.String(length=32), nullable=False
    )
    # The one scope of ``scope_type`` the preset's role is created in; NULL creates it
    # in every scope of the type.
    scope_id: Mapped[UUID | None] = mapped_column("scope_id", GUID(), nullable=True)
    # Default for the ``auto_assign`` flag copied onto roles instantiated from this preset.
    auto_assign: Mapped[bool] = mapped_column(
        "auto_assign", sa.Boolean, nullable=False, server_default=sa.false()
    )
    # Soft-delete flag. Toggled by the Delete / Restore service operations;
    # the Update API never mutates this column directly.
    deleted: Mapped[bool] = mapped_column(
        "deleted", sa.Boolean, nullable=False, server_default=sa.false()
    )
