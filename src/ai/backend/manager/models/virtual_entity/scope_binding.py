from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

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
    """Edge ``scope -> virtual_entity``: the scope is named by its own virtual entity node."""

    __tablename__ = "scope_bindings"
    __table_args__ = (
        sa.Index("ix_scope_bindings_scope", "scope_entity_id"),
        sa.Index(
            "ix_scope_bindings_virtual_entity",
            "virtual_entity_id",
            postgresql_include=["scope_entity_id", "permission_cap"],
        ),
    )

    virtual_entity_id: Mapped[VirtualEntityID] = mapped_column(
        "virtual_entity_id",
        GUID(VirtualEntityID),
        sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    scope_entity_id: Mapped[VirtualEntityID] = mapped_column(
        "scope_entity_id",
        GUID(VirtualEntityID),
        sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_cap: Mapped[Permission | None] = mapped_column(
        "permission_cap", IntFlagType(Permission), nullable=True
    )

    def to_data(self) -> ScopeBindingData:
        return ScopeBindingData(
            virtual_entity_id=self.virtual_entity_id,
            scope_entity_id=self.scope_entity_id,
            permission_cap=self.permission_cap,
        )
