from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Coroutine, Iterable, Sequence
from typing import Any

from ai.backend.appproxy.common.config import HostPortPair, SecretConfig
from ai.backend.appproxy.common.defs import (
    WORKER_AUTHORITY_LABEL,
    WORKER_INGRESS_DELIVERY_MODE_LABEL,
    WORKER_SERVICE_GROUP,
)
from ai.backend.appproxy.common.types import IngressDeliveryMode
from ai.backend.appproxy.coordinator.clients.worker.base import AbstractWorkerClient
from ai.backend.appproxy.coordinator.clients.worker.client import AppProxyWorkerClient
from ai.backend.appproxy.coordinator.clients.worker.traefik.client import TraefikWorkerClient
from ai.backend.appproxy.coordinator.errors.ingress import IngressPushFailedError
from ai.backend.common.clients.http_client.client_pool import ClientKey, ClientPool
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressAuthority, IngressKey
from ai.backend.common.exception import BackendAIError
from ai.backend.common.service_discovery.service_discovery import ServiceDiscovery


class IngressService:
    """Sends ingresses to the worker clients of their authority: Traefik when it is enabled,
    otherwise every api-delivery worker node. The coordinator keeps none of them."""

    _worker_service_discovery: ServiceDiscovery
    _client_pool: ClientPool
    _secrets: SecretConfig
    _traefik_worker_client: TraefikWorkerClient | None

    def __init__(
        self,
        worker_service_discovery: ServiceDiscovery,
        client_pool: ClientPool,
        secrets: SecretConfig,
        traefik_worker_client: TraefikWorkerClient | None,
    ) -> None:
        self._worker_service_discovery = worker_service_discovery
        self._client_pool = client_pool
        self._secrets = secrets
        self._traefik_worker_client = traefik_worker_client

    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        ingresses_by_authority: defaultdict[IngressAuthority, list[Ingress]] = defaultdict(list)
        for ingress in ingresses:
            ingresses_by_authority[ingress.authority].append(ingress)
        worker_clients_by_authority = await self._worker_clients_by_authority(
            ingresses_by_authority.keys()
        )
        await self._await_every_push([
            worker_client.upsert(ingresses_by_authority[authority])
            for authority, worker_clients in worker_clients_by_authority.items()
            for worker_client in worker_clients
        ])

    async def remove(self, keys: Sequence[IngressKey]) -> None:
        keys_by_authority: defaultdict[IngressAuthority, list[IngressKey]] = defaultdict(list)
        for key in keys:
            keys_by_authority[key.authority].append(key)
        worker_clients_by_authority = await self._worker_clients_by_authority(
            keys_by_authority.keys()
        )
        await self._await_every_push([
            worker_client.remove(keys_by_authority[authority])
            for authority, worker_clients in worker_clients_by_authority.items()
            for worker_client in worker_clients
        ])

    async def _worker_clients_by_authority(
        self, authorities: Iterable[IngressAuthority]
    ) -> dict[IngressAuthority, list[AbstractWorkerClient]]:
        if self._traefik_worker_client is not None:
            return {authority: [self._traefik_worker_client] for authority in authorities}
        worker_addrs = await self._api_delivery_worker_addrs(authorities)
        return {
            authority: [self._api_delivery_worker_client(addr) for addr in addrs]
            for authority, addrs in worker_addrs.items()
        }

    async def _await_every_push(self, push_tasks: Sequence[Coroutine[Any, Any, None]]) -> None:
        # Raising before every push settles would let a late push undo the caller's next request.
        results = await asyncio.gather(*push_tasks, return_exceptions=True)
        failures = [result for result in results if isinstance(result, BaseException)]
        if failures:
            raise IngressPushFailedError(
                extra_data={
                    "failures": [
                        failure.body_dict
                        if isinstance(failure, BackendAIError)
                        else {"title": repr(failure)}
                        for failure in failures
                    ]
                },
            ) from BaseExceptionGroup("ingress pushes failed", failures)

    def _api_delivery_worker_client(self, addr: HostPortPair) -> AppProxyWorkerClient:
        session = self._client_pool.load_client_session(
            ClientKey(endpoint=f"http://{addr}", domain="appproxy-worker")
        )
        return AppProxyWorkerClient(session, addr, self._secrets)

    async def _api_delivery_worker_addrs(
        self, authorities: Iterable[IngressAuthority]
    ) -> dict[IngressAuthority, list[HostPortPair]]:
        try:
            worker_services = await self._worker_service_discovery.get_service_group(
                WORKER_SERVICE_GROUP
            )
        except ValueError:
            # RedisServiceDiscovery raises ValueError for a group with no registered service.
            worker_services = []
        requested_authorities = set(authorities)
        worker_addrs: defaultdict[IngressAuthority, list[HostPortPair]] = defaultdict(list)
        for worker_service in worker_services:
            delivery_mode = worker_service.labels.get(WORKER_INGRESS_DELIVERY_MODE_LABEL)
            authority = worker_service.labels.get(WORKER_AUTHORITY_LABEL)
            if delivery_mode == IngressDeliveryMode.API and authority in requested_authorities:
                worker_addrs[IngressAuthority(authority)].append(
                    HostPortPair(
                        host=worker_service.endpoint.address, port=worker_service.endpoint.port
                    )
                )
        return worker_addrs
