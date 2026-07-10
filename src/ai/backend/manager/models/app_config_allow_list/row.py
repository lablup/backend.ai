from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.app_config.types import AppConfigAccessLevel, AppConfigScopeType
from ai.backend.common.identifier.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.data.app_config_allow_list.types import (
    AppConfigAllowListData,
)
from ai.backend.manager.models.base import GUID, Base, StrEnumType

__all__ = ("AppConfigAllowListRow",)


class AppConfigAllowListRow(Base):  # type: ignore[misc]
    """Registration of one config layer: a ``(config_name, scope_type)`` and its access policy.

    A config fragment may exist only when a matching row exists here — the row *registers*
    the layer (it is not itself a write grant). Deletion cascades both ways: fragments
    reference this table by ``(config_name, scope_type)`` and this table references
    ``app_config_definitions`` by ``config_name``, both ``ON DELETE CASCADE`` — so retiring a
    config name clears its entries and fragments. ``rank`` is the merge priority the entry's
    fragments carry (low → high; higher wins) — admin-owned so fragment owners cannot
    re-order the merge. ``read_access`` / ``write_access`` are the admin-owned tiers deciding
    who may read / write the layer, keeping read-enablement and write-authorization
    independent of the row's mere existence. At most one row per ``(config_name, scope_type)``;
    only admins create or remove these rows.
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
        sa.ForeignKey("app_config_definitions.config_name", ondelete="CASCADE"),
        nullable=False,
    )
    scope_type: Mapped[AppConfigScopeType] = mapped_column(
        "scope_type",
        StrEnumType(AppConfigScopeType),
        nullable=False,
    )
    rank: Mapped[int] = mapped_column(
        "rank",
        sa.Integer,
        nullable=False,
    )
    read_access: Mapped[AppConfigAccessLevel] = mapped_column(
        "read_access",
        StrEnumType(AppConfigAccessLevel),
        nullable=False,
    )
    write_access: Mapped[AppConfigAccessLevel] = mapped_column(
        "write_access",
        StrEnumType(AppConfigAccessLevel),
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
            rank=self.rank,
            read_access=self.read_access,
            write_access=self.write_access,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
