"""The kernel group's environ, one row per key."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironID
from ai.backend.common.data.environ.types import ENVIRON_KEY_PATTERN
from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.models.base import GUID, Base

__all__ = ("KernelGroupEnvironRow",)


class KernelGroupEnvironRow(Base):
    """Per-group environment variable, unique on (kernel_group_id, key)."""

    __tablename__ = "kernel_group_environ"
    __table_args__ = (
        sa.UniqueConstraint("kernel_group_id", "key"),
        sa.CheckConstraint(
            f"key ~ '{ENVIRON_KEY_PATTERN}'",
            name="key_is_environ_name",
        ),
    )

    id: Mapped[KernelGroupEnvironID] = mapped_column(
        "id",
        GUID(KernelGroupEnvironID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    kernel_group_id: Mapped[KernelGroupID] = mapped_column(
        "kernel_group_id",
        GUID(KernelGroupID),
        sa.ForeignKey("kernel_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column("key", sa.String(length=256), nullable=False)
    value: Mapped[str] = mapped_column("value", sa.Text, nullable=False)

    def to_data(self) -> KernelGroupEnvironData:
        return KernelGroupEnvironData(
            id=self.id,
            kernel_group_id=self.kernel_group_id,
            key=self.key,
            value=self.value,
        )
