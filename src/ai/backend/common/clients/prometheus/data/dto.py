import enum
from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, override

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .response import QueryResponseData, Result, ResultMetric, ResultValue


class ResultType(enum.Enum):
    MATRIX = "matrix"
    VECTOR = "vector"
    SCALAR = "scalar"
    STRING = "string"


class PrometheusResultMetric(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    value_type: str
    name: Optional[str] = Field(
        default=None,
        validation_alias="__name__",
        examples=["backendai_device_utilization", "backendai_container_utilization"],
    )
    agent_id: Optional[str] = Field(default=None)
    container_metric_name: Optional[str] = Field(default=None)
    instance: Optional[str] = Field(default=None)
    job: Optional[str] = Field(default=None)
    kernel_id: Optional[str] = Field(default=None)
    owner_project_id: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("project_id", "owner_project_id")
    )
    service_group: Optional[str] = Field(default=None)
    service_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    owner_user_id: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("user_id", "owner_user_id")
    )
    version: Optional[str] = Field(default=None)

    device_metric_name: Optional[str] = Field(default=None)
    device_id: Optional[str] = Field(default=None)

    def to_metric(self) -> ResultMetric:
        return ResultMetric(
            value_type=self.value_type,
            name=self.name,
            agent_id=self.agent_id,
            container_metric_name=self.container_metric_name,
            instance=self.instance,
            job=self.job,
            kernel_id=self.kernel_id,
            owner_project_id=self.owner_project_id,
            service_group=self.service_group,
            service_id=self.service_id,
            session_id=self.session_id,
            owner_user_id=self.owner_user_id,
            version=self.version,
            device_metric_name=self.device_metric_name,
            device_id=self.device_id,
        )


class ResultValuePair(NamedTuple):
    timestamp: float
    value: str

    def to_result_value(self) -> ResultValue:
        return ResultValue(timestamp=self.timestamp, value=self.value)


class AbstractResult(ABC):
    @abstractmethod
    def to_result(self) -> Result:
        raise NotImplementedError


class MatrixResult(AbstractResult, BaseModel):
    metric: PrometheusResultMetric
    values: list[ResultValuePair]

    @override
    def to_result(self) -> Result:
        return Result(
            metric=self.metric.to_metric(),
            values=[value.to_result_value() for value in self.values],
        )


class VectorResult(AbstractResult, BaseModel):
    metric: PrometheusResultMetric
    value: ResultValuePair

    @override
    def to_result(self) -> Result:
        return Result(metric=self.metric.to_metric(), values=[self.value.to_result_value()])


class ScalarResult(AbstractResult, BaseModel):
    value: ResultValuePair

    @override
    def to_result(self) -> Result:
        return Result(metric=None, values=[self.value.to_result_value()])


class StringResult(AbstractResult, BaseModel):
    value: ResultValuePair

    @override
    def to_result(self) -> Result:
        return Result(metric=None, values=[self.value.to_result_value()])


class PrometheusResponseData(BaseModel):
    model_config = ConfigDict(validate_by_alias=True)

    result_type: ResultType = Field(validation_alias="resultType")
    result: list = Field(default_factory=list)


class PrometheusResponse(BaseModel):
    data: PrometheusResponseData
    status: str

    def to_response_data(self) -> QueryResponseData:
        match self.data.result_type:
            case ResultType.MATRIX:
                return QueryResponseData(
                    [MatrixResult.model_validate(item).to_result() for item in self.data.result],
                )
            case ResultType.VECTOR:
                return QueryResponseData(
                    [VectorResult.model_validate(item).to_result() for item in self.data.result],
                )
            case ResultType.SCALAR:
                return QueryResponseData(
                    [ScalarResult.model_validate(item).to_result() for item in self.data.result],
                )
            case ResultType.STRING:
                return QueryResponseData(
                    [StringResult.model_validate(item).to_result() for item in self.data.result],
                )
