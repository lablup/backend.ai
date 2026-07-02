from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.permission.virtual_scope import AssociationEntityData
from ai.backend.common.entity.types import EntityType
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IntFlagType,
)


class AssociationEntityRow(Base):  # type: ignore[misc]
    __tablename__ = "association_entity"
    __table_args__ = (
        sa.Index("ix_association_entity_entity", "entity_type", "entity_id"),
        sa.UniqueConstraint(
            "virtual_scope_id", "entity_type", "entity_id", name="uq_association_entity_vs_entity"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    virtual_scope_id: Mapped[VirtualScopeID] = mapped_column(
        "virtual_scope_id",
        GUID(VirtualScopeID),
        sa.ForeignKey("virtual_scope.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", sa.String(length=32), nullable=False
    )
    entity_id: Mapped[str] = mapped_column("entity_id", sa.String(length=64), nullable=False)
    permission_cap: Mapped[Permission | None] = mapped_column(
        "permission_cap", IntFlagType(Permission), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    def to_data(self) -> AssociationEntityData:
        return AssociationEntityData(
            virtual_scope_id=self.virtual_scope_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            permission_cap=self.permission_cap,
        )
