from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.data.app_config_allow_list.types import (
    AppConfigAllowListData,
    AppConfigScopeType,
)
from ai.backend.manager.models.base import GUID, Base, StrEnumType

__all__ = ("AppConfigAllowListRow",)


class AppConfigAllowListRow(Base):  # type: ignore[misc]
    """Permission to write config fragments for one config name at one scope type.

    A config fragment may be created, updated, or purged only when a matching row
    exists here; without one, the write is rejected. Reads never consult this table.
    There is at most one row per ``(config_name, scope_type)``, and only admins
    create or remove these rows.
    """

    __tablename__ = "app_config_allow_list"
    __table_args__ = (
        sa.UniqueConstraint(
            "config_name", "scope_type", name="uq_app_config_allow_list_config_name_scope_type"
        ),
    )

    id: Mapped[AppConfigAllowListID] = mapped_column(
        "id",
        GUID(AppConfigAllowListID),
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

    def to_data(self) -> AppConfigAllowListData:
        return AppConfigAllowListData(
            id=self.id,
            config_name=self.config_name,
            scope_type=self.scope_type,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
