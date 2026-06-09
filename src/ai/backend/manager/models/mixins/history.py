"""Shared mixin for reconcile history rows (session/deployment/route/replica group).

Holds the columns common to every history table and the single merge rule. Category
and the entity FK stay on each row (not universal); the merge rule does not use them —
category only scopes which row is read as the latest.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Self

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.session.types import SubStepResult
from ai.backend.manager.models.base import GUID, PydanticListColumn


class ReconcileHistoryMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    phase: Mapped[str] = mapped_column("phase", sa.String(length=64), nullable=False)
    from_status: Mapped[str | None] = mapped_column(
        "from_status", sa.String(length=64), nullable=True
    )
    to_status: Mapped[str | None] = mapped_column("to_status", sa.String(length=64), nullable=True)

    result: Mapped[str] = mapped_column("result", sa.String(length=32), nullable=False)
    error_code: Mapped[str | None] = mapped_column(
        "error_code", sa.String(length=128), nullable=True
    )
    message: Mapped[str] = mapped_column("message", sa.Text, nullable=False)

    sub_steps: Mapped[list[SubStepResult]] = mapped_column(
        "sub_steps",
        PydanticListColumn(SubStepResult),
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    )

    attempts: Mapped[int] = mapped_column("attempts", sa.Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    def should_merge_with(self, other: Self) -> bool:
        """Merge a repeated transition onto the latest row when phase/status/error match.

        Category is not compared here — the latest row is already read within the same
        category, so a match means the same transition is recurring.
        """
        return (
            self.phase == other.phase
            and self.from_status == other.from_status
            and self.to_status == other.to_status
            and self.error_code == other.error_code
        )
