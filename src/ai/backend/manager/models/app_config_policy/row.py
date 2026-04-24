from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.base import GUID, Base


class AppConfigPolicyRow(Base):  # type: ignore[misc]
    __tablename__ = "app_config_policies"
    __table_args__ = (
        sa.UniqueConstraint(
            "config_name",
            name="uq_app_config_policies_config_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    # `config_name` is the FK target referenced by `app_config_fragments.name`
    # (BEP-1052 §1). It is immutable — updates that attempt to change it
    # are rejected at the service layer; the FK's ON UPDATE NO ACTION
    # default is the backstop.
    config_name: Mapped[str] = mapped_column(
        "config_name",
        sa.String(length=128),
        nullable=False,
    )
    # Ordered scope chain, low → high merge priority. Doubles as the
    # write allow-list. Stored as `String[]` so adding a scope does
    # not require a migration. Values mirror `AppConfigScopeType`.
    scope_sources: Mapped[Sequence[str]] = mapped_column(
        "scope_sources",
        sa.ARRAY(sa.String(length=64)),
        nullable=False,
        server_default="{}",
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=True,
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
