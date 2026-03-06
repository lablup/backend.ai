"""Adapter for converting Prometheus Query Preset domain data to DTOs."""

from __future__ import annotations

from ai.backend.common.dto.clients.prometheus.response import MetricResponse
from ai.backend.common.dto.manager.prometheus_query_preset import (
    MetricLabelEntryDTO,
    MetricValueDTO,
    PresetDTO,
    PresetMetricResult,
    PresetOptionsDTO,
)
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData


class PrometheusQueryPresetAdapter:
    """Adapter for converting between domain data and DTOs."""

    def convert_to_dto(self, data: PrometheusQueryPresetData) -> PresetDTO:
        """Convert domain data to DTO."""
        return PresetDTO(
            id=data.id,
            name=data.name,
            metric_name=data.metric_name,
            query_template=data.query_template,
            time_window=data.time_window,
            options=PresetOptionsDTO(
                filter_labels=data.filter_labels,
                group_labels=data.group_labels,
            ),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    def convert_metric_response(self, response: MetricResponse) -> PresetMetricResult:
        """Convert a Prometheus MetricResponse to a PresetMetricResult DTO."""
        metric_labels = [
            MetricLabelEntryDTO(key=key, value=str(val))
            for key, val in response.metric.model_dump(exclude_none=True).items()
        ]
        values = [MetricValueDTO(timestamp=ts, value=v) for ts, v in response.values]
        return PresetMetricResult(metric=metric_labels, values=values)
