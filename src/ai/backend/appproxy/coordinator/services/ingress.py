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
from ai.backend.appproxy.coordinator.clients.worker.client import AppProxyWorkerClient
from ai.backend.appproxy.coordinator.errors.ingress import ApiDeliveryWorkerPushFailedError
from ai.backend.common.clients.http_client.client_pool import ClientKey, ClientPool
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressAuthority, IngressKey
from ai.backend.common.exception import BackendAIError
from ai.backend.common.service_discovery.service_discovery import ServiceDiscovery


class IngressService:
    """Pushes ingresses to every api-delivery worker node of their authority, keeping none."""

    _service_discovery: ServiceDiscovery
    _client_pool: ClientPool
    _secrets: SecretConfig

    def __init__(
        self,
        service_discovery: ServiceDiscovery,
        client_pool: ClientPool,
        secrets: SecretConfig,
    ) -> None:
        self._service_discovery = service_discovery
        self._client_pool = client_pool
        self._secrets = secrets

    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        by_authority: defaultdict[IngressAuthority, list[Ingress]] = defaultdict(list)
        for ingress in ingresses:
            by_authority[ingress.authority].append(ingress)
        worker_addrs = await self._api_delivery_worker_addrs(by_authority.keys())
        await self._await_every_push([
            self._worker_client(addr).upsert(by_authority[authority])
            for authority, addrs in worker_addrs.items()
            for addr in addrs
        ])

    async def remove(self, keys: Sequence[IngressKey]) -> None:
        by_authority: defaultdict[IngressAuthority, list[IngressKey]] = defaultdict(list)
        for key in keys:
            by_authority[key.authority].append(key)
        worker_addrs = await self._api_delivery_worker_addrs(by_authority.keys())
        await self._await_every_push([
            self._worker_client(addr).remove(by_authority[authority])
            for authority, addrs in worker_addrs.items()
            for addr in addrs
        ])

    async def _await_every_push(self, push_tasks: Sequence[Coroutine[Any, Any, None]]) -> None:
        # Raising before every push settles would let a late push undo the caller's next request.
        results = await asyncio.gather(*push_tasks, return_exceptions=True)
        failures = [result for result in results if isinstance(result, BaseException)]
        if failures:
            raise ApiDeliveryWorkerPushFailedError(
                extra_data={
                    "failures": [
                        failure.body_dict
                        if isinstance(failure, BackendAIError)
                        else {"title": repr(failure)}
                        for failure in failures
                    ]
                },
            ) from BaseExceptionGroup("api-delivery worker pushes failed", failures)

    def _worker_client(self, addr: HostPortPair) -> AppProxyWorkerClient:
        session = self._client_pool.load_client_session(
            ClientKey(endpoint=f"http://{addr}", domain="appproxy-worker")
        )
        return AppProxyWorkerClient(session, addr, self._secrets)

    async def _api_delivery_worker_addrs(
        self, authorities: Iterable[IngressAuthority]
    ) -> dict[IngressAuthority, list[HostPortPair]]:
        try:
            workers = await self._service_discovery.get_service_group(WORKER_SERVICE_GROUP)
        except ValueError:
            # RedisServiceDiscovery raises ValueError for a group with no registered service.
            workers = []
        requested_authorities = set(authorities)
        worker_addrs: defaultdict[IngressAuthority, list[HostPortPair]] = defaultdict(list)
        for worker in workers:
            delivery_mode = worker.labels.get(WORKER_INGRESS_DELIVERY_MODE_LABEL)
            authority = worker.labels.get(WORKER_AUTHORITY_LABEL)
            if delivery_mode == IngressDeliveryMode.API and authority in requested_authorities:
                worker_addrs[IngressAuthority(authority)].append(
                    HostPortPair(host=worker.endpoint.address, port=worker.endpoint.port)
                )
        return worker_addrs
