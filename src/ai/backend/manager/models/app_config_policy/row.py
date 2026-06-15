from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID
from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.base import GUID, Base, StrEnumType


class AppConfigPolicyRow(Base):  # type: ignore[misc]
    __tablename__ = "app_config_policies"
    __table_args__ = (
        sa.UniqueConstraint(
            "config_name",
            name="uq_app_config_policies_config_name",
        ),
    )

    id: Mapped[AppConfigPolicyID] = mapped_column(
        "id",
        GUID(AppConfigPolicyID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    # `config_name` is the FK target referenced by `app_config_fragments.name`.
    # It is immutable — updates that attempt to change it are rejected at the
    # service layer.
    config_name: Mapped[str] = mapped_column(
        "config_name",
        sa.String(length=128),
        nullable=False,
    )
    # Ordered scope chain intended to drive merge priority (low → high) and to
    # double as the per-scope write allow-list.
    scope_sources: Mapped[Sequence[AppConfigScopeType]] = mapped_column(
        "scope_sources",
        sa.ARRAY(StrEnumType(AppConfigScopeType, length=64)),
        nullable=False,
        server_default="{}",
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

    def to_data(self) -> AppConfigPolicyData:
        return AppConfigPolicyData(
            id=self.id,
            config_name=self.config_name,
            scope_sources=list(self.scope_sources),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
