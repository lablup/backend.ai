from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.permission.virtual_entity import EntityMembershipData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IntFlagType,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class EntityMembershipRow(CreatedAtMixin, Base):
    __tablename__ = "entity_memberships"
    __table_args__ = (
        sa.Index(
            "ix_entity_memberships_entity",
            "entity_type",
            "entity_id",
            postgresql_include=["virtual_entity_id", "permission_cap"],
        ),
    )

    virtual_entity_id: Mapped[VirtualEntityID] = mapped_column(
        "virtual_entity_id",
        GUID(VirtualEntityID),
        sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", sa.String(length=32), primary_key=True
    )
    entity_id: Mapped[EntityID] = mapped_column("entity_id", GUID(), primary_key=True)
    permission_cap: Mapped[Permission | None] = mapped_column(
        "permission_cap", IntFlagType(Permission), nullable=True
    )

    def to_data(self) -> EntityMembershipData:
        return EntityMembershipData(
            virtual_entity_id=self.virtual_entity_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            permission_cap=self.permission_cap,
        )
