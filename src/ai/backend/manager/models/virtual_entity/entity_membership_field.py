from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.id import EntityMembershipCapID, FieldPath
from ai.backend.manager.models.base import GUID, Base


class EntityMembershipFieldRow(Base):
    """A path a cap row without ``all_fields`` lets its bit through on; the bit is
    the parent's."""

    __tablename__ = "entity_membership_fields"
    __table_args__ = (sa.CheckConstraint("path <> ''", name="path"),)

    cap_id: Mapped[EntityMembershipCapID] = mapped_column(
        "cap_id",
        GUID(EntityMembershipCapID),
        sa.ForeignKey("entity_membership_caps.id", ondelete="CASCADE"),
        primary_key=True,
    )
    path: Mapped[FieldPath] = mapped_column("path", sa.Text, primary_key=True)
