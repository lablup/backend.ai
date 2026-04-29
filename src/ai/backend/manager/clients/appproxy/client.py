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
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.request import (
    BulkCreateEndpointRequest,
    BulkDeleteEndpointRequest,
    BulkRegisterRoutesRequest,
    BulkUnregisterRoutesRequest,
    BulkUpdateRoutesRequest,
    MintEndpointTokenRequest,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.response import (
    BulkCreateEndpointResponse,
    BulkDeleteEndpointResponse,
    BulkRegisterRoutesResponse,
    BulkUnregisterRoutesResponse,
    BulkUpdateRoutesResponse,
    MintEndpointTokenResponse,
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
                "Accept": "application/json",
                "X-BackendAI-Token": self._token,
            },
        ) as resp:
            resp.raise_for_status()
            result: dict[str, Any] = await resp.json()
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
        async with self._client_session.post(
            "/v2/endpoints/bulk",
            json=body.model_dump(mode="json"),
            headers={
                "Accept": "application/json",
                "X-BackendAI-Token": self._token,
            },
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json()
            return BulkCreateEndpointResponse.model_validate(payload)

    @appproxy_client_resilience.apply()
    async def delete_endpoint(
        self,
        endpoint_id: UUID,
    ) -> None:
        async with self._client_session.delete(
            f"/v2/endpoints/{endpoint_id}",
            headers={
                "Accept": "application/json",
                "X-BackendAI-Token": self._token,
            },
        ):
            pass

    @appproxy_client_resilience.apply()
    async def bulk_update_routes(
        self,
        body: BulkUpdateRoutesRequest,
    ) -> BulkUpdateRoutesResponse:
        """Replace routing tables for many endpoints in a single coordinator call.

        AppProxy commits the new ``circuit.route_info`` set in one
        transaction and then propagates per circuit; per-entry failures
        (e.g. circuit not yet registered) come back in the response so
        the caller can retry on the next sync cycle without aborting
        the whole batch.
        """
        async with self._client_session.post(
            "/v2/endpoints/bulk/routes",
            json=body.model_dump(mode="json"),
            headers={
                "X-BackendAI-Token": self._token,
            },
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json()
            return BulkUpdateRoutesResponse.model_validate(payload)

    @appproxy_client_resilience.apply()
    async def bulk_register_routes(
        self,
        body: BulkRegisterRoutesRequest,
    ) -> BulkRegisterRoutesResponse:
        """Append new routes to many endpoints (delta semantics).

        Unlike :meth:`bulk_update_routes`, this only adds the supplied
        route entries to each circuit's existing ``route_info`` set. The
        coordinator dedupes by ``route_id`` so a redundant push is a
        no-op. Per-entry failures (e.g. circuit not yet registered)
        come back in the response so the caller can rely on the
        fallback long-cycle sync to converge state.
        """
        async with self._client_session.post(
            "/v2/endpoints/bulk/routes/register",
            json=body.model_dump(mode="json"),
            headers={
                "X-BackendAI-Token": self._token,
            },
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json()
            return BulkRegisterRoutesResponse.model_validate(payload)

    @appproxy_client_resilience.apply()
    async def bulk_unregister_routes(
        self,
        body: BulkUnregisterRoutesRequest,
    ) -> BulkUnregisterRoutesResponse:
        """Drop routes from many endpoints (delta semantics).

        The caller only sends the ``route_id`` set to remove. The
        coordinator drops each matching entry from
        ``circuit.route_info`` and reports already-absent ids as
        idempotent no-ops. Per-entry failures come back in the response
        so callers fall back to the long-cycle sync to converge state.
        """
        async with self._client_session.post(
            "/v2/endpoints/bulk/routes/unregister",
            json=body.model_dump(mode="json"),
            headers={
                "X-BackendAI-Token": self._token,
            },
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json()
            return BulkUnregisterRoutesResponse.model_validate(payload)

    @appproxy_client_resilience.apply()
    async def mint_endpoint_token(
        self,
        endpoint_id: UUID,
        body: MintEndpointTokenRequest,
    ) -> MintEndpointTokenResponse:
        """Ask the coordinator to issue a per-endpoint JWT.

        The worker's inference-frontend auth check requires a token
        signed with the shared ``jwt_secret`` and bound to the
        endpoint's circuit, so this is the only correct way to produce
        an Authorization: Bearer token for ``./bai deployment chat`` and
        peer SDK callers.
        """
        async with self._client_session.post(
            f"/v2/endpoints/{endpoint_id}/token",
            json=body.model_dump(mode="json"),
            headers={
                "X-BackendAI-Token": self._token,
            },
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json()
            return MintEndpointTokenResponse.model_validate(payload)

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
        async with self._client_session.request(
            "DELETE",
            "/v2/endpoints/bulk",
            json=body.model_dump(mode="json"),
            headers={
                "Accept": "application/json",
                "X-BackendAI-Token": self._token,
            },
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json()
            return BulkDeleteEndpointResponse.model_validate(payload)
