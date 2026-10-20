"""The kernel group's environ, one row per key."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.manager.models.base import GUID, Base

__all__ = ("KernelGroupEnvironRow",)


class KernelGroupEnvironRow(Base):
    """Per-group environment variable.

    Composite primary key: (kernel_group_id, key). The key format matches
    ``system_session_environ.key``.
    """

    __tablename__ = "kernel_group_environ"
    __table_args__ = (
        sa.CheckConstraint(
            "key ~ '^[A-Za-z_][A-Za-z0-9_]*$'",
            name="key_is_environ_name",
        ),
    )

    kernel_group_id: Mapped[KernelGroupID] = mapped_column(
        "kernel_group_id",
        GUID(KernelGroupID),
        sa.ForeignKey("kernel_groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    key: Mapped[str] = mapped_column("key", sa.String(length=256), primary_key=True)
    value: Mapped[str] = mapped_column("value", sa.Text, nullable=False)
