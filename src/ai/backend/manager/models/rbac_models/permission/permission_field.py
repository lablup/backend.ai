from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.id import FieldPath, PermissionID
from ai.backend.manager.models.base import GUID, Base


class PermissionFieldRow(Base):
    """A path a READ or UPDATE permission row is scoped to; the operation is the
    parent's. A parent with ``all_fields`` covers every field and has no rows
    here; one without covers exactly these paths and their descendants."""

    __tablename__ = "permission_fields"
    __table_args__ = (sa.CheckConstraint("path <> ''", name="ck_permission_fields_path"),)

    permission_id: Mapped[PermissionID] = mapped_column(
        "permission_id",
        GUID(PermissionID),
        sa.ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    path: Mapped[FieldPath] = mapped_column("path", sa.Text, primary_key=True)
