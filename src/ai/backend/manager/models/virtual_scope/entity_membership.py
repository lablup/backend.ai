from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.permission.virtual_scope import EntityMembershipData
from ai.backend.common.entity.types import EntityType
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IntFlagType,
)


class EntityMembershipRow(Base):  # type: ignore[misc]
    __tablename__ = "entity_memberships"
    __table_args__ = (sa.Index("ix_entity_memberships_entity", "entity_type", "entity_id"),)

    virtual_scope_id: Mapped[VirtualScopeID] = mapped_column(
        "virtual_scope_id",
        GUID(VirtualScopeID),
        sa.ForeignKey("virtual_scopes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", sa.String(length=32), primary_key=True
    )
    entity_id: Mapped[str] = mapped_column("entity_id", sa.String(length=64), primary_key=True)
    permission_cap: Mapped[Permission | None] = mapped_column(
        "permission_cap", IntFlagType(Permission), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    def to_data(self) -> EntityMembershipData:
        return EntityMembershipData(
            virtual_scope_id=self.virtual_scope_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            permission_cap=self.permission_cap,
        )
