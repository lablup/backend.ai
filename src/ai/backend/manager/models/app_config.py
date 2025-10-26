from __future__ import annotations

import logging
from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.app_config.types import AppConfigData, AppConfigScopeType

from .base import Base, IDColumn

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__: Sequence[str] = (
    "AppConfigScopeType",
    "AppConfigRow",
)


class AppConfigRow(Base):
    __tablename__ = "app_configs"

    id = IDColumn()
    scope_type = sa.Column(
        "scope_type",
        sa.Enum(AppConfigScopeType, name="app_config_scope_type"),
        nullable=False,
        index=True,
    )
    scope_id = sa.Column("scope_id", sa.String(length=256), nullable=False, index=True)
    extra_config = sa.Column("extra_config", pgsql.JSONB, nullable=False, default={})
    created_at = sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    modified_at = sa.Column(
        "modified_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.current_timestamp(),
    )

    __table_args__ = (sa.UniqueConstraint("scope_type", "scope_id", name="uq_app_configs_scope"),)

    def to_data(self) -> AppConfigData:
        return AppConfigData(
            id=self.id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            extra_config=self.extra_config,
            created_at=self.created_at,
            modified_at=self.modified_at,
        )
