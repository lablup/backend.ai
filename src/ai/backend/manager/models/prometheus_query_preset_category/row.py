from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("PrometheusQueryPresetCategoryRow",)


class PrometheusQueryPresetCategoryRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
    __tablename__ = "prometheus_query_preset_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)

    def to_data(self) -> PrometheusQueryPresetCategoryData:
        return PrometheusQueryPresetCategoryData(
            id=self.id,
            name=self.name,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
