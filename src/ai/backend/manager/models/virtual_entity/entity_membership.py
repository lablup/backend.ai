from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.id import EntityMembershipID
from ai.backend.common.data.permission.virtual_entity import EntityMembershipData
from ai.backend.manager.models.base import (
    GUID,
    Base,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class EntityMembershipRow(CreatedAtMixin, Base):
    """Edge ``virtual_entity -> member``: both ends are virtual entity nodes.

    A belonging edge is not capped. A share is: its ceiling is the edge's
    ``entity_membership_caps`` rows, none meaning a cap of zero."""

    __tablename__ = "entity_memberships"
    __table_args__ = (
        sa.UniqueConstraint(
            "virtual_entity_id", "member_entity_id", name="uq_entity_memberships_edge"
        ),
        sa.Index(
            "ix_entity_memberships_entity",
            "member_entity_id",
            postgresql_include=["virtual_entity_id", "capped"],
        ),
    )

    id: Mapped[EntityMembershipID] = mapped_column(
        "id",
        GUID(EntityMembershipID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    virtual_entity_id: Mapped[VirtualEntityID] = mapped_column(
        "virtual_entity_id",
        GUID(VirtualEntityID),
        sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    member_entity_id: Mapped[VirtualEntityID] = mapped_column(
        "member_entity_id",
        GUID(VirtualEntityID),
        sa.ForeignKey("virtual_entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    capped: Mapped[bool] = mapped_column(
        "capped", sa.Boolean, nullable=False, server_default=sa.false()
    )

    def to_data(self) -> EntityMembershipData:
        return EntityMembershipData(
            virtual_entity_id=self.virtual_entity_id,
            member_entity_id=self.member_entity_id,
            capped=self.capped,
        )
