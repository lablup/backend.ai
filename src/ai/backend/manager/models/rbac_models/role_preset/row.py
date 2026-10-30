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
from ai.backend.manager.models.mixins.soft_delete import SoftDeleteMixin
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin


class RolePresetRow(SoftDeleteMixin, LifecycleTimestampsMixin, Base):
    __tablename__ = "role_presets"
    __table_args__ = (
        sa.Index(
            "ix_role_presets_scope_type_deleted_at",
            "scope_type",
            "deleted_at",
        ),
        # One preset name per scope. Soft-deleted rows count too, because restoring
        # a preset brings it back under its old name.
        sa.UniqueConstraint(
            "name",
            "scope_type",
            "scope_id",
            # scope_id is NULL for a preset that applies to every scope of its type.
            # PostgreSQL treats NULLs as distinct by default, which would let two such
            # presets share a name.
            postgresql_nulls_not_distinct=True,
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
    # Whether a personal project's owner is mapped to the role made from this preset.
    auto_assign_to_owner: Mapped[bool] = mapped_column(
        "auto_assign_to_owner", sa.Boolean, nullable=False, server_default=sa.false()
    )
