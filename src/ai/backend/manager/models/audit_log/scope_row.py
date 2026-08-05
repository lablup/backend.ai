from __future__ import annotations

import uuid
from typing import override

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.models.base import GUID, Base

__all__ = ("AuditLogScopeRow",)


class AuditLogScopeRow(Base):  # type: ignore[misc]
    """A scope the audited entity belongs to.

    An entity can sit in several scopes at once, so scopes live here rather than as
    columns on ``audit_logs`` — one affected entity stays one audit row no matter how
    many scopes matched it. Only scope actions write these; read the action's shape
    from ``audit_logs.action_kind``, never from whether these rows exist.
    """

    __tablename__ = "audit_log_scopes"
    __table_args__ = (
        sa.UniqueConstraint("audit_log_id", "scope_type", "scope_id", name="uq_audit_log_scope"),
        sa.Index("ix_audit_log_scopes_scope", "scope_type", "scope_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    audit_log_id: Mapped[uuid.UUID] = mapped_column(
        "audit_log_id",
        GUID,
        sa.ForeignKey("audit_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_type: Mapped[str] = mapped_column("scope_type", sa.String, nullable=False)
    scope_id: Mapped[str] = mapped_column("scope_id", sa.String, nullable=False)

    def __init__(
        self,
        audit_log_id: uuid.UUID,
        scope_type: str,
        scope_id: str | uuid.UUID,
    ) -> None:
        self.audit_log_id = audit_log_id
        self.scope_type = scope_type
        self.scope_id = str(scope_id) if isinstance(scope_id, uuid.UUID) else scope_id

    @override
    def __str__(self) -> str:
        return (
            f"AuditLogScopeRow("
            f"audit_log_id: {self.audit_log_id}, "
            f"scope_type: {self.scope_type}, "
            f"scope_id: {self.scope_id}"
            f")"
        )

    @override
    def __repr__(self) -> str:
        return self.__str__()
