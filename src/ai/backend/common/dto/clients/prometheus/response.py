from typing import Any

from pydantic import ConfigDict, Field, model_validator

from ai.backend.common.types import BackendAISchema


class MetricResponseInfo(BackendAISchema):
    """Metric information from Prometheus response."""

    value_type: str | None = Field(default=None)
    name: str | None = Field(default=None, validation_alias="__name__")
    agent_id: str | None = Field(default=None)
    container_metric_name: str | None = Field(default=None)
    instance: str | None = Field(default=None)
    job: str | None = Field(default=None)
    kernel_id: str | None = Field(default=None)
    owner_project_id: str | None = Field(default=None)
    owner_user_id: str | None = Field(default=None)
    session_id: str | None = Field(default=None)

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    @property
    def has_container_metric_labels(self) -> bool:
        """Check if all required labels for container metric processing are present."""
        return (
            self.kernel_id is not None
            and self.container_metric_name is not None
            and self.value_type is not None
        )


type MetricResponseValue = tuple[float, str]  # (timestamp, value)


class MetricResponse(BackendAISchema):
    """Single metric result from a Prometheus query.

    Handles both instant queries (single ``value``) and range queries
    (list of ``values``) by normalizing the instant form into a one-element list.
    """

    metric: MetricResponseInfo
    values: list[MetricResponseValue]

    @model_validator(mode="before")
    @classmethod
    def _normalize_values(cls, data: Any) -> Any:
        if isinstance(data, dict) and "value" in data and "values" not in data:
            data["values"] = [data.pop("value")]
        return data


class PrometheusQueryData(BackendAISchema):
    """Data field from a Prometheus query response."""

    result_type: str = Field(validation_alias="resultType")
    result: list[MetricResponse]

    model_config = ConfigDict(populate_by_name=True)


class PrometheusResponse(BackendAISchema):
    """Response from Prometheus query API (instant or range)."""

    status: str
    data: PrometheusQueryData


class LabelValueResponse(BackendAISchema):
    """Response from Prometheus label values API."""

    status: str
    data: list[str]
