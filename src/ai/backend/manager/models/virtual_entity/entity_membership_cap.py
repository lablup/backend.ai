from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.id import EntityMembershipCapID, EntityMembershipID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.base import GUID, Base, IntFlagType


class EntityMembershipCapRow(Base):
    """One operation bit a capped membership edge lets through. With ``all_fields``
    the bit passes on every field; without, on the ``entity_membership_fields``
    paths and their descendants."""

    __tablename__ = "entity_membership_caps"
    __table_args__ = (
        sa.UniqueConstraint("membership_id", "permission", name="uq_entity_membership_caps_bit"),
        sa.CheckConstraint(
            "permission > 0 AND (permission & (permission - 1)) = 0", name="single_bit"
        ),
        sa.CheckConstraint("all_fields OR permission IN (1, 2)", name="field_scope"),
    )

    id: Mapped[EntityMembershipCapID] = mapped_column(
        "id",
        GUID(EntityMembershipCapID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    membership_id: Mapped[EntityMembershipID] = mapped_column(
        "membership_id",
        GUID(EntityMembershipID),
        sa.ForeignKey("entity_memberships.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission: Mapped[Permission] = mapped_column(
        "permission", IntFlagType(Permission), nullable=False
    )
    all_fields: Mapped[bool] = mapped_column(
        "all_fields", sa.Boolean, nullable=False, server_default=sa.true()
    )
