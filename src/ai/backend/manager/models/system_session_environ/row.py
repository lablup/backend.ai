from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.system_session_environ import (
    SystemSessionEnvironID,
    SystemSessionEnvironScopeID,
)
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("SystemSessionEnvironRow",)

_ENVIRON_KEY_PATTERN: Final = r"^[A-Za-z_][A-Za-z0-9_]*$"


class SystemSessionEnvironRow(LifecycleTimestampsMixin, Base):
    """One value injected under ``key`` into every session of the scope."""

    __tablename__ = "system_session_environ"
    __table_args__ = (
        sa.UniqueConstraint(
            "key",
            "scope_type",
            "scope_id",
            postgresql_nulls_not_distinct=True,
        ),
        sa.CheckConstraint(
            "(scope_type = 'global') = (scope_id IS NULL)",
            name="scope_id_matches_scope_type",
        ),
        sa.CheckConstraint(
            f"key ~ '{_ENVIRON_KEY_PATTERN}'",
            name="key_is_environ_name",
        ),
        sa.Index("ix_system_session_environ_scope", "scope_type", "scope_id"),
    )

    id: Mapped[SystemSessionEnvironID] = mapped_column(
        "id",
        GUID(SystemSessionEnvironID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    value_source: Mapped[SystemSessionEnvironValueSource] = mapped_column(
        "value_source",
        StrEnumType(SystemSessionEnvironValueSource),
        nullable=False,
    )
    key: Mapped[str] = mapped_column("key", sa.String(length=256), nullable=False)
    scope_type: Mapped[SystemSessionEnvironScopeType] = mapped_column(
        "scope_type",
        StrEnumType(SystemSessionEnvironScopeType),
        nullable=False,
    )
    scope_id: Mapped[SystemSessionEnvironScopeID | None] = mapped_column(
        "scope_id",
        GUID(SystemSessionEnvironScopeID),
        nullable=True,
    )
    disabled: Mapped[bool] = mapped_column(
        "disabled", sa.Boolean, nullable=False, server_default=sa.false()
    )

    def to_data(self) -> SystemSessionEnvironData:
        return SystemSessionEnvironData(
            id=self.id,
            value_source=self.value_source,
            key=self.key,
            scope_id=self.scope_type.to_owner(self.scope_id),
            disabled=self.disabled,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
