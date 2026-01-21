from typing import Any
from uuid import UUID

import aiohttp

from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience

from .types import CreateEndpointRequestBody

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
            return await resp.json()

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
