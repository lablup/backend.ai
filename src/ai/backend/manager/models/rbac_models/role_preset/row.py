from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

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
            "ix_role_presets_scope_type_auto_apply",
            "scope_type",
            postgresql_where=sa.text("auto_apply IS TRUE"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(64), nullable=False)
    scope_type: Mapped[ScopeType] = mapped_column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=False
    )
    # If true, this preset is auto-applied when a scope of `scope_type` is created.
    auto_apply: Mapped[bool] = mapped_column(
        "auto_apply", sa.Boolean, nullable=False, server_default=sa.false()
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
