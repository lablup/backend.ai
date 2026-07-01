from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.base import GUID, Base

__all__ = ("PrometheusQueryPresetCategoryRow",)


class PrometheusQueryPresetCategoryRow(Base):  # type: ignore[misc]
    __tablename__ = "prometheus_query_preset_categories"

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
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    def to_data(self) -> PrometheusQueryPresetCategoryData:
        return PrometheusQueryPresetCategoryData(
            id=self.id,
            name=self.name,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
