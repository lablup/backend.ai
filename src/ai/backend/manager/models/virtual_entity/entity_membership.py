from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

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
    """Edge ``virtual_entity -> member``: both ends are virtual entity nodes."""

    __tablename__ = "entity_memberships"
    __table_args__ = (
        sa.Index(
            "ix_entity_memberships_entity",
            "member_entity_id",
            postgresql_include=["virtual_entity_id", "permission_cap"],
        ),
    )

    virtual_entity_id: Mapped[VirtualEntityID] = mapped_column(
        "virtual_entity_id",
        GUID(VirtualEntityID),
        sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    member_entity_id: Mapped[VirtualEntityID] = mapped_column(
        "member_entity_id",
        GUID(VirtualEntityID),
        sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_cap: Mapped[Permission | None] = mapped_column(
        "permission_cap", IntFlagType(Permission), nullable=True
    )

    def to_data(self) -> EntityMembershipData:
        return EntityMembershipData(
            virtual_entity_id=self.virtual_entity_id,
            member_entity_id=self.member_entity_id,
            permission_cap=self.permission_cap,
        )
