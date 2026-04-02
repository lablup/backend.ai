from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.base import GUID, Base

__all__ = ("RuntimeVariantRow",)


class RuntimeVariantRow(Base):  # type: ignore[misc]
    __tablename__ = "runtime_variants"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=True,
        onupdate=sa.func.now(),
    )

    def to_data(self) -> RuntimeVariantData:
        return RuntimeVariantData(
            id=self.id,
            name=self.name,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
