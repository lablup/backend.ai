"""The kernel_groups table: one role of a session and the execution spec its kernels share.

The group's resource request lives in ``kernel_group_resource_slot/row.py`` and its
environ in ``kernel_group_environ/row.py``.
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.kernel_group import KernelGroupID, KernelGroupRole
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = ("KernelGroupRow",)


class KernelGroupRow(CreatedAtMixin, Base):
    """One role of a session, frozen at enqueue.

    The replica count is not stored: it is the number of kernels whose
    ``kernel_group_id`` points here.
    """

    __tablename__ = "kernel_groups"
    __table_args__ = (sa.UniqueConstraint("session_id", "role"),)

    id: Mapped[KernelGroupID] = mapped_column(
        "id",
        GUID(KernelGroupID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    session_id: Mapped[SessionID] = mapped_column(
        "session_id",
        GUID(SessionID),
        sa.ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[KernelGroupRole] = mapped_column("role", sa.String(length=16), nullable=False)
    image_id: Mapped[ImageID | None] = mapped_column(
        "image_id",
        GUID(ImageID),
        sa.ForeignKey("images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Bytes of the requested ``mem`` the container may use as /dev/shm. NULL means the
    # runtime default. Not a slot: the agent sets it as ShmSize and allocates nothing.
    shmem: Mapped[int | None] = mapped_column("shmem", sa.BigInteger, nullable=True)
    startup_command: Mapped[str | None] = mapped_column("startup_command", sa.Text, nullable=True)
    bootstrap_script: Mapped[str | None] = mapped_column("bootstrap_script", sa.Text, nullable=True)
    preopen_ports: Mapped[list[int]] = mapped_column(
        "preopen_ports",
        sa.ARRAY(sa.Integer),
        nullable=False,
        default=list,
        server_default=sa.text("'{}'"),
    )
    requested_starts_at: Mapped[datetime | None] = mapped_column(
        "requested_starts_at", sa.DateTime(timezone=True), nullable=True
    )
    batch_timeout_sec: Mapped[int | None] = mapped_column(
        "batch_timeout_sec", sa.Integer, nullable=True
    )
