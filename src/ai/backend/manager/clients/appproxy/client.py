from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

import aiohttp
import aiotools

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.common import InternalServerError

from .types import CreateEndpointRequestBody

log: BraceStyleAdapter = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

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


class AppProxyClient:
    _client_session: aiohttp.ClientSession
    _address: str
    _token: str

    def __init__(self, client_session: aiohttp.ClientSession, address: str, token: str) -> None:
        self._client_session = client_session
        self._address = address
        self._token = token

    @staticmethod
    @aiotools.lru_cache(expire_after=30)  # expire after 30 seconds
    async def query_status(
        appproxy_addr: str,
    ) -> dict[str, Any]:
        """Query the status of an app-proxy (wsproxy) at the given address."""
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                appproxy_addr + "/status",
                headers={"Accept": "application/json"},
            ) as resp,
        ):
            try:
                result = await resp.json()
            except (aiohttp.ContentTypeError, json.JSONDecodeError) as e:
                log.error("Failed to parse app-proxy status response from {}: {}", appproxy_addr, e)
                raise InternalServerError(
                    "Got invalid response from app-proxy when querying status"
                ) from e
            return result

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
