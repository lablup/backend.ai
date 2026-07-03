from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.permission.virtual_scope import ScopeBindingData
from ai.backend.common.entity.types import ScopeType
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IntFlagType,
)


class ScopeBindingRow(Base):  # type: ignore[misc]
    __tablename__ = "scope_bindings"
    __table_args__ = (
        sa.Index("ix_scope_bindings_scope", "scope_type", "scope_id"),
        sa.UniqueConstraint(
            "virtual_scope_id", "scope_type", "scope_id", name="uq_scope_bindings_vs_scope"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    virtual_scope_id: Mapped[VirtualScopeID] = mapped_column(
        "virtual_scope_id",
        GUID(VirtualScopeID),
        sa.ForeignKey("virtual_scopes.id", ondelete="CASCADE"),
        nullable=False,
    )
    scope_type: Mapped[ScopeType] = mapped_column(
        "scope_type", sa.String(length=32), nullable=False
    )
    scope_id: Mapped[str] = mapped_column("scope_id", sa.String(length=64), nullable=False)
    permission_cap: Mapped[Permission | None] = mapped_column(
        "permission_cap", IntFlagType(Permission), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    def to_data(self) -> ScopeBindingData:
        return ScopeBindingData(
            virtual_scope_id=self.virtual_scope_id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            permission_cap=self.permission_cap,
        )
