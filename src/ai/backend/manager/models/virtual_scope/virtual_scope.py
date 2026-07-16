from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import ScopeType
from ai.backend.common.data.permission.virtual_scope import VirtualScopeData
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.common.identifier.virtual_scope import VirtualScopeID
from ai.backend.manager.models.base import (
    GUID,
    Base,
)


class VirtualScopeRow(Base):  # type: ignore[misc]
    __tablename__ = "virtual_scopes"
    __table_args__ = (
        sa.UniqueConstraint("scope_type", "scope_id", name="uq_virtual_scopes_scope"),
    )

    id: Mapped[VirtualScopeID] = mapped_column(
        "id",
        GUID(VirtualScopeID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    # Identifies the origin scope this virtual scope represents.
    scope_type: Mapped[ScopeType] = mapped_column(
        "scope_type", sa.String(length=32), nullable=False
    )
    scope_id: Mapped[ScopeID] = mapped_column("scope_id", GUID(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    def to_data(self) -> VirtualScopeData:
        return VirtualScopeData(
            id=self.id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
        )
