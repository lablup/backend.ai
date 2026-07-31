from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.permission.virtual_scope import EntityMembershipData
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IntFlagType,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class EntityMembershipRow(CreatedAtMixin, Base):  # type: ignore[misc]
    __tablename__ = "entity_memberships"
    __table_args__ = (
        sa.Index(
            "ix_entity_memberships_entity",
            "entity_type",
            "entity_id",
            postgresql_include=["virtual_scope_id", "permission_cap"],
        ),
    )

    virtual_scope_id: Mapped[VirtualScopeID] = mapped_column(
        "virtual_scope_id",
        GUID(VirtualScopeID),
        sa.ForeignKey("virtual_scopes.id", ondelete="CASCADE"),
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
            virtual_scope_id=self.virtual_scope_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            permission_cap=self.permission_cap,
        )
