from __future__ import annotations

import uuid
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
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("AppConfigFragmentRow",)


class AppConfigFragmentRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
    """One scoped app config fragment — a single JSON document at ``(config_name, scope_type, scope_id)``.

    A fragment's merge priority is its allow-list entry's ``rank`` — the fragment
    row carries no rank of its own.
    """

    __tablename__ = "app_config_fragments"
    __table_args__ = (
        sa.UniqueConstraint(
            "config_name",
            "scope_type",
            "scope_id",
            name="uq_app_config_fragments_config_name_scope_type_scope_id",
        ),
        # The constraint above only covers domain and user fragments: Postgres counts NULLs
        # as distinct, so it would let a config take any number of public fragments. This
        # partial index restores that guarantee for the NULL (public) rows. It replaces the
        # NULLS NOT DISTINCT the constraint would otherwise want, which needs Postgres 15+.
        sa.Index(
            "uq_app_config_fragments_public_config_name",
            "config_name",
            "scope_type",
            unique=True,
            postgresql_where=sa.text("scope_id IS NULL"),
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
        nullable=False,
    )
    scope_type: Mapped[AppConfigScopeType] = mapped_column(
        "scope_type",
        StrEnumType(AppConfigScopeType),
        nullable=False,
    )
    # NULL is the public scope: it has no owner. Domain and user fragments carry the id of
    # the domain or user that owns them.
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        "scope_id",
        GUID,
        nullable=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        "config",
        JSONB,
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
