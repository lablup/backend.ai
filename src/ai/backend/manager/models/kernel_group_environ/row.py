"""The kernel group's environ, one row per key."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.manager.data.environ.types import ENVIRON_KEY_PATTERN
from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.models.base import GUID, Base

__all__ = ("KernelGroupEnvironRow",)


class KernelGroupEnvironRow(Base):
    """Per-group environment variable.

    Composite primary key: (kernel_group_id, key).
    """

    __tablename__ = "kernel_group_environ"
    __table_args__ = (
        sa.CheckConstraint(
            f"key ~ '{ENVIRON_KEY_PATTERN}'",
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

    def to_data(self) -> KernelGroupEnvironData:
        return KernelGroupEnvironData(
            kernel_group_id=self.kernel_group_id,
            key=self.key,
            value=self.value,
        )
