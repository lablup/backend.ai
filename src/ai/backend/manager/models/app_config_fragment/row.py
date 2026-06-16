from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID
from ai.backend.manager.data.app_config_fragment.types import (
    AppConfigFragmentData,
    AppConfigScopeType,
)
from ai.backend.manager.models.base import GUID, Base, StrEnumType


class AppConfigFragmentRow(Base):  # type: ignore[misc]
    __tablename__ = "app_config_fragments"
    __table_args__ = (
        sa.UniqueConstraint(
            "scope_type",
            "scope_id",
            "name",
            name="uq_app_config_fragments_scope_name",
        ),
        sa.Index("ix_app_config_fragments_name_rank", "name", "rank"),
    )

    id: Mapped[AppConfigFragmentID] = mapped_column(
        GUID(AppConfigFragmentID), primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    scope_type: Mapped[AppConfigScopeType] = mapped_column(
        "scope_type",
        StrEnumType(AppConfigScopeType, length=32),
        nullable=False,
        index=True,
    )
    scope_id: Mapped[str] = mapped_column(
        "scope_id",
        sa.String(length=255),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        "name",
        sa.String(length=128),
        nullable=False,
    )
    # Merge priority within a `name` (low → high). Assigned by next-value
    # (`MAX(rank) + gap` within the `name`) on create, like DeploymentRevisionPreset.
    rank: Mapped[int] = mapped_column(
        "rank",
        sa.Integer,
        nullable=False,
    )
    config: Mapped[Mapping[str, Any] | None] = mapped_column(
        "config",
        pgsql.JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    )

    def to_data(self) -> AppConfigFragmentData:
        return AppConfigFragmentData(
            id=self.id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            name=self.name,
            rank=self.rank,
            config=dict(self.config) if self.config is not None else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
