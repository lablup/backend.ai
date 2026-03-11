from abc import ABC, abstractmethod
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field


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


class BaseMetricResponse(BaseModel, ABC):
    """Base class for Prometheus metric results."""

    metric: MetricResponseInfo

    @property
    @abstractmethod
    def metric_values(self) -> list[MetricResponseValue]: ...


class MetricResponse(BaseMetricResponse):
    """Single metric result from Prometheus range query."""

    values: list[MetricResponseValue]

    @property
    def metric_values(self) -> list[MetricResponseValue]:
        return self.values


class MetricInstantResponse(BaseMetricResponse):
    """Single metric result from Prometheus instant query."""

    value: MetricResponseValue

    @property
    def metric_values(self) -> list[MetricResponseValue]:
        return [self.value]


class BasePrometheusQueryData(BaseModel, ABC):
    """Base class for Prometheus query data."""

    result_type: str = Field(validation_alias="resultType")

    model_config = ConfigDict(populate_by_name=True)

    @property
    @abstractmethod
    def metric_results(self) -> Sequence[BaseMetricResponse]: ...


class PrometheusQueryData(BasePrometheusQueryData):
    """Data field from Prometheus query_range response."""

    result: list[MetricResponse]

    @property
    def metric_results(self) -> Sequence[BaseMetricResponse]:
        return self.result


class PrometheusQueryInstantData(BasePrometheusQueryData):
    """Data field from Prometheus instant query response."""

    result: list[MetricInstantResponse]

    @property
    def metric_results(self) -> Sequence[BaseMetricResponse]:
        return self.result


class BasePrometheusQueryResponse(BaseModel, ABC):
    """Base class for Prometheus query responses."""

    status: str

    @property
    @abstractmethod
    def query_data(self) -> BasePrometheusQueryData: ...


class PrometheusQueryRangeResponse(BasePrometheusQueryResponse):
    """Response from Prometheus query_range API."""

    data: PrometheusQueryData

    @property
    def query_data(self) -> BasePrometheusQueryData:
        return self.data


class PrometheusQueryInstantResponse(BasePrometheusQueryResponse):
    """Response from Prometheus instant query API."""

    data: PrometheusQueryInstantData

    @property
    def query_data(self) -> BasePrometheusQueryData:
        return self.data


class LabelValueResponse(BaseModel):
    """Response from Prometheus label values API."""

    status: str
    data: list[str]
