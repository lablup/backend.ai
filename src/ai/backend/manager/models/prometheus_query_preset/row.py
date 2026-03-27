from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    PydanticColumn,
)

__all__ = ("PrometheusQueryPresetRow",)


class PresetOptions(BaseModel):
    filter_labels: list[str]
    group_labels: list[str]

    model_config = ConfigDict(frozen=True)


class PrometheusQueryPresetRow(Base):  # type: ignore[misc]
    __tablename__ = "prometheus_query_presets"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column("name", sa.String(length=256), nullable=False)
    metric_name: Mapped[str] = mapped_column("metric_name", sa.String(length=256), nullable=False)
    query_template: Mapped[str] = mapped_column("query_template", sa.Text, nullable=False)
    time_window: Mapped[str | None] = mapped_column(
        "time_window", sa.String(length=32), nullable=True
    )
    options: Mapped[PresetOptions] = mapped_column(
        "options",
        PydanticColumn(PresetOptions),
        nullable=False,
        server_default=sa.text('\'{"filter_labels":[],"group_labels":[]}\'::jsonb'),
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
        onupdate=sa.func.now(),
    )

    def to_data(self) -> PrometheusQueryPresetData:
        """Convert Row to domain model data."""
        return PrometheusQueryPresetData(
            id=self.id,
            name=self.name,
            metric_name=self.metric_name,
            query_template=self.query_template,
            time_window=self.time_window,
            filter_labels=self.options.filter_labels,
            group_labels=self.options.group_labels,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
