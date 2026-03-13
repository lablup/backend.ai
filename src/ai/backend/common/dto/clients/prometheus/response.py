from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MetricResponseInfo(BaseModel):
    """Metric information from Prometheus response."""

    value_type: str
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


type MetricResponseValue = tuple[float, str]  # (timestamp, value)


class MetricResponse(BaseModel):
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


class PrometheusQueryData(BaseModel):
    """Data field from a Prometheus query response."""

    result_type: str = Field(validation_alias="resultType")
    result: list[MetricResponse]

    model_config = ConfigDict(populate_by_name=True)


class PrometheusResponse(BaseModel):
    """Response from Prometheus query API (instant or range)."""

    status: str
    data: PrometheusQueryData


class LabelValueResponse(BaseModel):
    """Response from Prometheus label values API."""

    status: str
    data: list[str]
