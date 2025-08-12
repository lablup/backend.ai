from typing import Any

import aiohttp
import yarl

from ai.backend.common.clients.http_client.client_pool import ClientConfig, ClientKey, ClientPool

from .data.dto import PrometheusResponse
from .data.request import QueryData
from .data.response import QueryResponseData
from .exception import PrometheusException, ResultNotFound


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
