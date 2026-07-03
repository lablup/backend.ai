from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
)
from ai.backend.manager.models.base import GUID, Base, StrEnumType

__all__ = ("AppConfigFragmentRow",)


class AppConfigFragmentRow(Base):  # type: ignore[misc]
    """One scoped app config fragment — a single JSON document at ``(config_name, scope_type, scope_id)``.

    A fragment hangs off its ``app_config_allow_list`` entry (FK on
    ``(config_name, scope_type)``, ``ON DELETE CASCADE``): it exists only while the
    entry does, and its merge priority is the entry's ``rank`` — the fragment row
    carries no rank of its own.
    """

    __tablename__ = "app_config_fragments"
    __table_args__ = (
        sa.UniqueConstraint(
            "config_name",
            "scope_type",
            "scope_id",
            name="uq_app_config_fragments_config_name_scope_type_scope_id",
        ),
        sa.ForeignKeyConstraint(
            ["config_name", "scope_type"],
            ["app_config_allow_list.config_name", "app_config_allow_list.scope_type"],
            name="fk_app_config_fragments_config_name_scope_type",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[AppConfigFragmentID] = mapped_column(
        "id",
        GUID(AppConfigFragmentID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    config_name: Mapped[str] = mapped_column(
        "config_name",
        sa.String(length=128),
        sa.ForeignKey("app_config_definitions.config_name", ondelete="NO ACTION"),
        nullable=False,
    )
    scope_type: Mapped[AppConfigScopeType] = mapped_column(
        "scope_type",
        StrEnumType(AppConfigScopeType),
        nullable=False,
    )
    scope_id: Mapped[str] = mapped_column(
        "scope_id",
        sa.String(length=255),
        nullable=False,
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        "config",
        JSONB,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    def to_data(self) -> AppConfigFragmentData:
        return AppConfigFragmentData(
            id=self.id,
            config_name=self.config_name,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            config=self.config,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
