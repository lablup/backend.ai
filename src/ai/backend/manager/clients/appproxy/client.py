from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

import aiohttp

from ai.backend.appproxy.coordinator.api.types import AppProxyStatusResponse
from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
    tcp_client_session_factory,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.appproxy import AppProxyConnectionError, AppProxyResponseError

from .types import CreateEndpointRequestBody

log: BraceStyleAdapter = BraceStyleAdapter(logging.getLogger(__spec__.name))

appproxy_client_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.CLIENT, layer=LayerType.WSPROXY_CLIENT)),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class AppProxyClientPool:
    _client_pool: ClientPool

    def __init__(self) -> None:
        self._client_pool = ClientPool(tcp_client_session_factory)

    def load_client(self, address: str, token: str) -> AppProxyClient:
        client_session = self._client_pool.load_client_session(
            ClientKey(
                endpoint=address,
                domain="appproxy",
            )
        )
        return AppProxyClient(client_session, address, token)

    async def close(self) -> None:
        await self._client_pool.close()


class AppProxyClient:
    _client_session: aiohttp.ClientSession
    _address: str
    _token: str

    def __init__(self, client_session: aiohttp.ClientSession, address: str, token: str) -> None:
        self._client_session = client_session
        self._address = address
        self._token = token

    @appproxy_client_resilience.apply()
    async def fetch_status(self) -> AppProxyStatusResponse:
        try:
            async with self._client_session.get(
                "/status",
                headers={"Accept": "application/json"},
            ) as resp:
                data = await resp.json()
                return AppProxyStatusResponse.model_validate(data)
        except aiohttp.ClientConnectorError as e:
            log.error("Failed to connect to app-proxy at {}: {}", self._address, e)
            raise AppProxyConnectionError(
                extra_msg=f"Failed to connect to AppProxy at {self._address}"
            ) from e
        except (aiohttp.ContentTypeError, json.JSONDecodeError) as e:
            log.error("Failed to parse app-proxy status response from {}: {}", self._address, e)
            raise AppProxyResponseError(
                extra_msg=f"Invalid response from AppProxy at {self._address}"
            ) from e

    @appproxy_client_resilience.apply()
    async def create_endpoint(
        self,
        endpoint_id: UUID,
        body: CreateEndpointRequestBody,
    ) -> dict[str, Any]:
        async with self._client_session.post(
            f"/v2/endpoints/{endpoint_id}",
            json=body.model_dump(mode="json"),
            headers={
                "X-BackendAI-Token": self._token,
            },
        ) as resp:
            resp.raise_for_status()
            result: dict[str, Any] = await resp.json()
            return result

    @appproxy_client_resilience.apply()
    async def delete_endpoint(
        self,
        endpoint_id: UUID,
    ) -> None:
        async with self._client_session.delete(
            f"/v2/endpoints/{endpoint_id}",
            headers={
                "X-BackendAI-Token": self._token,
            },
        ):
            pass
