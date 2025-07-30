import enum
from abc import ABC, abstractmethod
from typing import Any, NamedTuple, Optional, override

import aiohttp
import yarl
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from ai.backend.common.clients.http_client.client_pool import ClientConfig, ClientKey, ClientPool

from .data.request import QueryData
from .data.response import QueryResponseData, Result, ResultMetric, ResultValue
from .exception import PrometheusException, ResultNotFound


class ResultType(enum.Enum):
    MATRIX = "matrix"
    VECTOR = "vector"
    SCALAR = "scalar"
    STRING = "string"


class _ResultMetric(BaseModel):
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


class _ResultValuePair(NamedTuple):
    timestamp: float
    value: str

    def to_result_value(self) -> ResultValue:
        return ResultValue(timestamp=self.timestamp, value=self.value)


class AbstractResult(ABC):
    @abstractmethod
    def to_result(self) -> Result:
        raise NotImplementedError


class MatrixResult(AbstractResult, BaseModel):
    metric: _ResultMetric
    values: list[_ResultValuePair]

    @override
    def to_result(self) -> Result:
        return Result(
            metric=self.metric.to_metric(),
            values=[value.to_result_value() for value in self.values],
        )


class VectorResult(AbstractResult, BaseModel):
    metric: _ResultMetric
    value: _ResultValuePair

    @override
    def to_result(self) -> Result:
        return Result(metric=self.metric.to_metric(), values=[self.value.to_result_value()])


class ScalarResult(AbstractResult, BaseModel):
    value: _ResultValuePair

    @override
    def to_result(self) -> Result:
        return Result(metric=None, values=[self.value.to_result_value()])


class StringResult(AbstractResult, BaseModel):
    value: _ResultValuePair

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


class PrometheusHTTPClient:
    def __init__(self, endpoint: yarl.URL, timewindow: str) -> None:
        self._endpoint = endpoint
        self._timewindow = timewindow
        self._client_pool = ClientPool(ClientConfig())

    async def close(self) -> None:
        await self._client_pool.close()

    def _load_client(self, address: str) -> aiohttp.ClientSession:
        return self._client_pool.load_client_session(ClientKey(address, "utilization"))

    def _to_aiohttp_form_data(self, data: QueryData) -> aiohttp.FormData:
        form_data = aiohttp.FormData()
        form_data.add_field("query", data.query)
        if data.start is not None:
            form_data.add_field("start", data.start)
        if data.end is not None:
            form_data.add_field("end", data.end)
        if data.step is not None:
            form_data.add_field("step", data.step)
        return form_data

    def _validate_response_data(self, data: Any) -> QueryResponseData:
        validated = PrometheusResponse.model_validate(data)
        return validated.to_response_data()

    async def _query(self, data: QueryData) -> QueryResponseData:
        address = self._endpoint / "query"
        client = self._load_client(str(address))
        form_data = self._to_aiohttp_form_data(data)
        async with client.post(address, data=form_data) as response:
            match response.status // 100:
                case 2:
                    raw_data = await response.json()
                    return self._validate_response_data(raw_data)
                case 4:
                    raise ResultNotFound(f"No results found for query: {data.query}")
                case _:
                    raise PrometheusException(
                        f"Failed to query utilization metrics: {response.status}"
                    )

    async def _query_range(self, data: QueryData) -> QueryResponseData:
        address = self._endpoint / "query_range"
        client = self._load_client(str(address))
        form_data = self._to_aiohttp_form_data(data)
        async with client.post(address, data=form_data) as response:
            match response.status // 100:
                case 2:
                    raw_data = await response.json()
                    return self._validate_response_data(raw_data)
                case 4:
                    raise ResultNotFound(f"No results found for query: {data.query}")
                case _:
                    raise PrometheusException(
                        f"Failed to query utilization metrics: {response.status}"
                    )
