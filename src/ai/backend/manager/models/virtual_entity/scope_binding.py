from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import ScopeID, ScopeType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.permission.virtual_entity import ScopeBindingData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IntFlagType,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class ScopeBindingRow(CreatedAtMixin, Base):
    __tablename__ = "scope_bindings"
    __table_args__ = (
        sa.Index("ix_scope_bindings_scope", "scope_type", "scope_id"),
        sa.Index(
            "ix_scope_bindings_virtual_entity",
            "virtual_entity_id",
            postgresql_include=["scope_type", "scope_id", "permission_cap"],
        ),
    )

    virtual_entity_id: Mapped[VirtualEntityID] = mapped_column(
        "virtual_entity_id",
        GUID(VirtualEntityID),
        sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    scope_type: Mapped[ScopeType] = mapped_column(
        "scope_type", sa.String(length=32), primary_key=True
    )
    scope_id: Mapped[ScopeID] = mapped_column("scope_id", GUID(), primary_key=True)
    permission_cap: Mapped[Permission | None] = mapped_column(
        "permission_cap", IntFlagType(Permission), nullable=True
    )

    def to_data(self) -> ScopeBindingData:
        return ScopeBindingData(
            virtual_entity_id=self.virtual_entity_id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            permission_cap=self.permission_cap,
        )
