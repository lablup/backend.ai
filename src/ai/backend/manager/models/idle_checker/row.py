from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckerSpec, IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.models.base import GUID, Base, PydanticColumn, StrEnumType
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin, UpdatedAtMixin


class IdleCheckerRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
    __tablename__ = "idle_checkers"
    __table_args__ = (
        sa.CheckConstraint(
            "initial_grace_period_seconds >= 0",
            name="initial_grace_period_seconds_non_negative",
        ),
    )

    id: Mapped[IdleCheckerID] = mapped_column(
        "id", GUID(IdleCheckerID), primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=128), nullable=False)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    checker_type: Mapped[CheckerType] = mapped_column(
        "checker_type", StrEnumType(CheckerType), nullable=False
    )
    target_session_types: Mapped[list[SessionTypes]] = mapped_column(
        "target_session_types",
        sa.ARRAY(StrEnumType(SessionTypes, use_name=True)),
        nullable=False,
    )
    initial_grace_period_seconds: Mapped[int] = mapped_column(
        "initial_grace_period_seconds",
        sa.Integer(),
        nullable=False,
        default=0,
    )
    spec: Mapped[IdleCheckerSpec] = mapped_column(
        "spec", PydanticColumn(IdleCheckerSpec), nullable=False
    )


class IdleCheckerBindingRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
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
    idle_checker_id: Mapped[IdleCheckerID] = mapped_column(
        "idle_checker_id", GUID(IdleCheckerID), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(
        "enabled", sa.Boolean, nullable=False, server_default=sa.true()
    )


class SessionIdleCheckRow(UpdatedAtMixin, Base):  # type: ignore[misc]
    __tablename__ = "session_idle_checks"
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name="fk_session_idle_checks_session_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["idle_checker_id"],
            ["idle_checkers.id"],
            name="fk_session_idle_checks_idle_checker_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "session_id",
            "idle_checker_id",
            name="pk_session_idle_checks",
        ),
        sa.Index(
            "ix_session_idle_checks_expire_at_not_null",
            "expire_at",
            postgresql_where=sa.text("expire_at IS NOT NULL"),
        ),
    )

    session_id: Mapped[SessionId] = mapped_column("session_id", GUID(SessionId), nullable=False)
    idle_checker_id: Mapped[IdleCheckerID] = mapped_column(
        "idle_checker_id", GUID(IdleCheckerID), nullable=False
    )
    expire_at: Mapped[datetime] = mapped_column(
        "expire_at", sa.DateTime(timezone=True), nullable=False
    )
    last_status: Mapped[IdleCheckPhase] = mapped_column(
        "last_status", StrEnumType(IdleCheckPhase), nullable=False
    )
    last_message: Mapped[str] = mapped_column("last_message", sa.Text, nullable=False)
