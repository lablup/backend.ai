from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.data.permission.types import ScopeType
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)


class RolePresetRow(Base):  # type: ignore[misc]
    __tablename__ = "role_presets"
    __table_args__ = (
        sa.Index(
            "uq_role_presets_scope_type_active",
            "scope_type",
            unique=True,
            postgresql_where=sa.text("deleted IS FALSE"),
        ),
    )

    id: Mapped[RolePresetID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(64), nullable=False)
    scope_type: Mapped[ScopeType] = mapped_column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=False
    )
    # Default for the ``auto_assign`` flag copied onto roles instantiated from this preset.
    auto_assign: Mapped[bool] = mapped_column(
        "auto_assign", sa.Boolean, nullable=False, server_default=sa.false()
    )
    # Soft-delete flag. The partial unique index above keeps at most one row
    # with ``deleted = false`` per ``scope_type``; deleted rows are archived.
    deleted: Mapped[bool] = mapped_column(
        "deleted", sa.Boolean, nullable=False, server_default=sa.false()
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
