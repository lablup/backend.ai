from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import Any
from uuid import UUID

import aiohttp

from ai.backend.appproxy.coordinator.api.types import AppProxyStatusResponse
from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
    tcp_client_session_factory,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.request import (
    BulkCreateEndpointRequest,
    BulkDeleteEndpointRequest,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.response import (
    BulkCreateEndpointResponse,
    BulkDeleteEndpointResponse,
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

    @asynccontextmanager
    async def _request(
        self,
        method: str,
        path: str,
        *,
        operation: str,
        json_body: Any = None,
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        """Issue an authenticated request and translate transport errors.

        Connection failures become ``AppProxyConnectionError``. Non-2xx
        responses become ``AppProxyResponseError`` with the upstream body
        attached as ``extra_data`` so a structured ``BackendAIError``
        payload returned by the coordinator survives the translation.
        """
        try:
            async with self._client_session.request(
                method,
                path,
                headers={
                    "Accept": "application/json",
                    "X-BackendAI-Token": self._token,
                },
                json=json_body,
            ) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    try:
                        error_body: Any = json.loads(text) if text else None
                    except json.JSONDecodeError:
                        error_body = text
                    log.error(
                        "AppProxy at {} returned {} during {}: {!r}",
                        self._address,
                        resp.status,
                        operation,
                        error_body,
                    )
                    raise AppProxyResponseError(
                        extra_msg=(f"AppProxy returned HTTP {resp.status} during {operation}"),
                        extra_data={"status": resp.status, "body": error_body},
                    )
                yield resp
        except aiohttp.ClientConnectorError as e:
            log.error(
                "Failed to connect to AppProxy at {} during {}: {}",
                self._address,
                operation,
                e,
            )
            raise AppProxyConnectionError(
                extra_msg=f"Failed to connect to AppProxy at {self._address}"
            ) from e

    async def _parse_json(
        self,
        resp: aiohttp.ClientResponse,
        *,
        operation: str,
    ) -> Any:
        try:
            return await resp.json()
        except (aiohttp.ContentTypeError, json.JSONDecodeError) as e:
            log.error(
                "Failed to parse AppProxy {} response from {}: {}",
                operation,
                self._address,
                e,
            )
            raise AppProxyResponseError(
                extra_msg=(f"Invalid response from AppProxy at {self._address} during {operation}"),
            ) from e

    @appproxy_client_resilience.apply()
    async def create_endpoint(
        self,
        endpoint_id: UUID,
        body: CreateEndpointRequestBody,
    ) -> dict[str, Any]:
        async with self._request(
            "POST",
            f"/v2/endpoints/{endpoint_id}",
            operation="create_endpoint",
            json_body=body.model_dump(mode="json"),
        ) as resp:
            result: dict[str, Any] = await self._parse_json(resp, operation="create_endpoint")
            return result

    @appproxy_client_resilience.apply()
    async def create_endpoints_bulk(
        self,
        body: BulkCreateEndpointRequest,
    ) -> BulkCreateEndpointResponse:
        """Create or sync multiple endpoints in a single coordinator call.

        The coordinator processes all entries inside one transaction and
        initializes freshly created circuits with one propagation call,
        so this is the preferred way to register many deployments at
        once (e.g. from the deployment provisioning handler).
        """
        async with self._request(
            "POST",
            "/v2/endpoints/bulk",
            operation="create_endpoints_bulk",
            json_body=body.model_dump(mode="json"),
        ) as resp:
            payload = await self._parse_json(resp, operation="create_endpoints_bulk")
            return BulkCreateEndpointResponse.model_validate(payload)

    @appproxy_client_resilience.apply()
    async def delete_endpoint(
        self,
        endpoint_id: UUID,
    ) -> None:
        async with self._request(
            "DELETE",
            f"/v2/endpoints/{endpoint_id}",
            operation="delete_endpoint",
        ):
            pass

    @appproxy_client_resilience.apply()
    async def delete_endpoints_bulk(
        self,
        body: BulkDeleteEndpointRequest,
    ) -> BulkDeleteEndpointResponse:
        """Delete multiple endpoints in a single coordinator call.

        The coordinator continues past per-entry failures and returns a
        per-endpoint result in input order, so the caller can decide how
        to treat partial failures (retry, log, etc.).
        """
        async with self._request(
            "DELETE",
            "/v2/endpoints/bulk",
            operation="delete_endpoints_bulk",
            json_body=body.model_dump(mode="json"),
        ) as resp:
            payload = await self._parse_json(resp, operation="delete_endpoints_bulk")
            return BulkDeleteEndpointResponse.model_validate(payload)
