from __future__ import annotations

import uuid

import sqlalchemy as sa
from pydantic import ConfigDict
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.types import BackendAISchema
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.models.base import (
    GUID,
    Base,
    PydanticColumn,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("PrometheusQueryPresetRow",)


class PresetOptions(BackendAISchema):
    filter_labels: list[str]
    group_labels: list[str]

    model_config = ConfigDict(frozen=True)


class PrometheusQueryPresetRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
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
    description: Mapped[str | None] = mapped_column("description", sa.Text, nullable=True)
    rank: Mapped[int] = mapped_column(
        "rank", sa.Integer, nullable=False, server_default=sa.text("0")
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        "category_id",
        GUID,
        sa.ForeignKey("prometheus_query_preset_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    options: Mapped[PresetOptions] = mapped_column(
        "options",
        PydanticColumn(PresetOptions),
        nullable=False,
        server_default=sa.text('\'{"filter_labels":[],"group_labels":[]}\'::jsonb'),
    )

    def to_data(self) -> PrometheusQueryPresetData:
        """Convert Row to domain model data."""
        return PrometheusQueryPresetData(
            id=self.id,
            name=self.name,
            description=self.description,
            rank=self.rank,
            category_id=self.category_id,
            metric_name=self.metric_name,
            query_template=self.query_template,
            time_window=self.time_window,
            filter_labels=self.options.filter_labels,
            group_labels=self.options.group_labels,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
