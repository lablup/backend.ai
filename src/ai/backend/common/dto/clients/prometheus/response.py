from pydantic import BaseModel, ConfigDict, Field


class MetricResponseInfo(BaseModel):
    """Metric information from Prometheus response."""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

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


type MetricResponseValue = tuple[float, str]  # (timestamp, value)


class MetricResponse(BaseModel):
    """Single metric result from Prometheus."""

    metric: MetricResponseInfo
    values: list[MetricResponseValue]


class PrometheusQueryData(BaseModel):
    """Data field from Prometheus query_range response."""

    model_config = ConfigDict(populate_by_name=True)

    result_type: str = Field(validation_alias="resultType")
    result: list[MetricResponse]


class PrometheusQueryRangeResponse(BaseModel):
    """Response from Prometheus query_range API."""

    status: str
    data: PrometheusQueryData


class LabelValueResponse(BaseModel):
    """Response from Prometheus label values API."""

    status: str
    data: list[str]
