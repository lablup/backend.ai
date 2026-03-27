from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.app_config.types import AppConfigData, AppConfigScopeType
from ai.backend.manager.models.base import GUID, Base

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__: Sequence[str] = (
    "AppConfigRow",
    "AppConfigScopeType",
)


class AppConfigRow(Base):  # type: ignore[misc]
    __tablename__ = "app_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    scope_type: Mapped[AppConfigScopeType] = mapped_column(
        "scope_type",
        sa.Enum(AppConfigScopeType, name="app_config_scope_type"),
        nullable=False,
        index=True,
    )
    scope_id: Mapped[str] = mapped_column(
        "scope_id", sa.String(length=256), nullable=False, index=True
    )
    extra_config: Mapped[Mapping[str, Any]] = mapped_column(
        "extra_config", pgsql.JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    modified_at: Mapped[datetime] = mapped_column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
        nullable=False,
    )

    __table_args__ = (sa.UniqueConstraint("scope_type", "scope_id", name="uq_app_configs_scope"),)

    def to_data(self) -> AppConfigData:
        return AppConfigData(
            id=self.id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            extra_config=dict(self.extra_config),
            created_at=self.created_at,
            modified_at=self.modified_at,
        )
