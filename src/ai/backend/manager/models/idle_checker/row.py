from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.models.base import GUID, ABCColumn, Base
from ai.backend.manager.models.idle_checker.spec import IdleCheckerSpecABC


class IdleCheckerRow(Base):  # type: ignore[misc]
    __tablename__ = "idle_checkers"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=128), nullable=False)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    checker_type: Mapped[str] = mapped_column("checker_type", sa.String(length=64), nullable=False)
    spec: Mapped[IdleCheckerSpecABC] = mapped_column(
        "spec", ABCColumn(IdleCheckerSpecABC), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        "modified_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


class IdleCheckerBindingRow(Base):  # type: ignore[misc]
    __tablename__ = "idle_checker_bindings"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["idle_checker_id"],
            ["idle_checkers.id"],
            name="fk_idle_checker_bindings_idle_checker_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "idle_checker_id",
            "scope_type",
            "scope_id",
            name="uq_idle_checker_bindings_checker_scope",
        ),
        sa.Index("ix_idle_checker_bindings_scope", "scope_type", "scope_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    scope_type: Mapped[str] = mapped_column("scope_type", sa.String(length=64), nullable=False)
    scope_id: Mapped[uuid.UUID] = mapped_column("scope_id", GUID, nullable=False)
    idle_checker_id: Mapped[uuid.UUID] = mapped_column("idle_checker_id", GUID, nullable=False)
    enabled: Mapped[bool] = mapped_column(
        "enabled", sa.Boolean, nullable=False, server_default=sa.true()
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        "modified_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )
