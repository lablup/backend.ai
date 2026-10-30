from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Collection, Iterable, Sequence
from dataclasses import dataclass
from typing import Final, override

from etcd_client import ClientError as EtcdClientError

from ai.backend.appproxy.common.defs import (
    WORKER_AUTHORITY_LABEL,
    WORKER_HOSTNAME_LABEL,
    WORKER_SERVICE_GROUP,
)
from ai.backend.appproxy.common.errors.service import WorkerNotFound
from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.common.types import WorkerFrontend
from ai.backend.appproxy.coordinator.clients.worker.base import AbstractWorkerClient
from ai.backend.appproxy.coordinator.clients.worker.traefik.routing_config import (
    TraefikRoutingConfigFactory,
)
from ai.backend.appproxy.coordinator.clients.worker.traefik.types import (
    AppliedIngressRevision,
    IngressRoutingConfigs,
)
from ai.backend.appproxy.coordinator.errors.ingress import (
    TraefikEtcdRequestFailedError,
    TraefikIngressConcurrentWriteError,
    TraefikIngressRevisionConflictError,
    TraefikIngressWriteFailedError,
)
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAuthority,
    IngressFrontendKey,
    IngressKey,
)
from ai.backend.common.service_discovery.service_discovery import ServiceDiscovery

# Outside every worker_{authority} root key, so Traefik never reads it.
_APPLIED_INGRESS_REVISIONS_ETCD_PREFIX: Final[str] = "applied_ingress_revisions"


@dataclass(frozen=True)
class TraefikWorkerClientArgs:
    etcd: TraefikEtcd
    worker_service_discovery: ServiceDiscovery
    routing_config_factory: TraefikRoutingConfigFactory
    max_concurrent_etcd_calls: int


class TraefikWorkerClient(AbstractWorkerClient):
    """Writes each ingress to Traefik etcd as one set of subtrees, replaced by the same or a newer
    revision. The revision is kept in etcd and guards the replacement transaction; a write that
    another write to the same frontend beats fails instead of retrying."""

    _etcd: TraefikEtcd
    _worker_service_discovery: ServiceDiscovery
    _routing_config_factory: TraefikRoutingConfigFactory
    _etcd_call_limit: asyncio.Semaphore

    def __init__(self, args: TraefikWorkerClientArgs) -> None:
        self._etcd = args.etcd
        self._worker_service_discovery = args.worker_service_discovery
        self._routing_config_factory = args.routing_config_factory
        self._etcd_call_limit = asyncio.Semaphore(args.max_concurrent_etcd_calls)

    @override
    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        """Writes nothing if any ingress is older than the revision etcd holds. Otherwise each
        ingress is written in its own transaction, so a failed write leaves the others written;
        the failures are raised together."""
        worker_frontends_by_authority = await self._worker_frontends_by_authority({
            ingress.authority for ingress in ingresses
        })
        applied_revisions_by_authority = await self._applied_revisions_by_authority(
            worker_frontends_by_authority.keys()
        )
        applied_revisions = [
            applied_revisions_by_authority[ingress.authority].get(ingress.frontend.key())
            for ingress in ingresses
        ]
        for ingress, applied_revision in zip(ingresses, applied_revisions, strict=True):
            if applied_revision is not None and applied_revision.revision > ingress.revision:
                raise TraefikIngressRevisionConflictError(
                    f"frontend {ingress.frontend.key()} holds revision {applied_revision.revision}, "
                    f"got {ingress.revision}",
                    extra_data={
                        "authority": ingress.authority,
                        "frontend_key": ingress.frontend.key(),
                    },
                )
        await self._run_ingress_transactions_concurrently(
            [ingress.key() for ingress in ingresses],
            [
                self._replace_routing_configs_and_revision(
                    ingress, worker_frontends_by_authority[ingress.authority], applied_revision
                )
                for ingress, applied_revision in zip(ingresses, applied_revisions, strict=True)
            ],
        )

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        await self._run_ingress_transactions_concurrently(
            keys, [self._clear_routing_configs_and_revision(ingress_key) for ingress_key in keys]
        )

    async def _clear_routing_configs_and_revision(self, ingress_key: IngressKey) -> None:
        emptied_subtrees_by_etcd_prefix = self._routing_config_factory.build_etcd_subtrees(
            ingress_key, IngressRoutingConfigs()
        )
        emptied_subtrees_by_etcd_prefix[self._applied_revision_etcd_key(ingress_key)] = {}
        async with self._etcd_call_limit:
            try:
                await self._etcd.atomic_replace_prefixes(emptied_subtrees_by_etcd_prefix)
            except EtcdClientError as e:
                raise TraefikEtcdRequestFailedError(
                    str(e),
                    extra_data={
                        "authority": ingress_key.authority,
                        "frontend_key": ingress_key.frontend_key,
                    },
                ) from e

    async def _replace_routing_configs_and_revision(
        self,
        ingress: Ingress,
        worker_frontend: WorkerFrontend,
        applied_revision: AppliedIngressRevision | None,
    ) -> None:
        ingress_key = ingress.key()
        routing_config_factory = self._routing_config_factory
        subtrees_by_etcd_prefix = routing_config_factory.build_etcd_subtrees(
            ingress_key, routing_config_factory.build_routing_configs(ingress, worker_frontend)
        )
        # The whole key is the replaced prefix: the frontend key one of another ingress starts
        # with ("port-1020" of "port-10205") must not reach this revision.
        subtrees_by_etcd_prefix[self._applied_revision_etcd_key(ingress_key)] = {
            "": str(ingress.revision)
        }
        applied_revision_guard = (
            str(applied_revision.revision) if applied_revision is not None else None
        )
        async with self._etcd_call_limit:
            try:
                replacement_committed = await self._etcd.compare_and_replace_prefixes(
                    subtrees_by_etcd_prefix,
                    guards={self._applied_revision_etcd_key(ingress_key): applied_revision_guard},
                )
            except EtcdClientError as e:
                raise TraefikEtcdRequestFailedError(
                    str(e),
                    extra_data={
                        "authority": ingress.authority,
                        "frontend_key": ingress.frontend.key(),
                    },
                ) from e
        if not replacement_committed:
            raise TraefikIngressConcurrentWriteError(
                f"frontend {ingress.frontend.key()} changed after revision {applied_revision_guard} "
                "was read",
                extra_data={
                    "authority": ingress.authority,
                    "frontend_key": ingress.frontend.key(),
                },
            )

    async def _run_ingress_transactions_concurrently(
        self,
        ingress_keys: Sequence[IngressKey],
        ingress_transactions: Sequence[Awaitable[None]],
    ) -> None:
        # One transaction per ingress: etcd caps a transaction's operations (--max-txn-ops, 128).
        # Every transaction settles before raising, or a late write could undo the next request.
        transaction_results = await asyncio.gather(*ingress_transactions, return_exceptions=True)
        failed_transactions = [
            (ingress_key, transaction_result)
            for ingress_key, transaction_result in zip(
                ingress_keys, transaction_results, strict=True
            )
            if isinstance(transaction_result, BaseException)
        ]
        if not failed_transactions:
            return
        raise TraefikIngressWriteFailedError(
            extra_data={
                "failed_ingresses": [
                    {"authority": ingress_key.authority, "frontend_key": ingress_key.frontend_key}
                    for ingress_key, _ in failed_transactions
                ]
            },
        ) from BaseExceptionGroup(
            "Traefik ingress writes failed", [failure for _, failure in failed_transactions]
        )

    async def _worker_frontends_by_authority(
        self, authorities: Iterable[IngressAuthority]
    ) -> dict[IngressAuthority, WorkerFrontend]:
        try:
            worker_services = await self._worker_service_discovery.get_service_group(
                WORKER_SERVICE_GROUP
            )
        except ValueError:
            # Service discovery raises ValueError for a group with no registered service.
            worker_services = []
        worker_service_labels_by_authority = {
            worker_service.labels[WORKER_AUTHORITY_LABEL]: worker_service.labels
            for worker_service in worker_services
            if WORKER_AUTHORITY_LABEL in worker_service.labels
        }
        worker_frontends_by_authority: dict[IngressAuthority, WorkerFrontend] = {}
        for authority in authorities:
            worker_service_labels = worker_service_labels_by_authority.get(authority)
            if worker_service_labels is None:
                raise WorkerNotFound(extra_data={"authority": authority})
            # A worker that registers no hostname label predates the Traefik labels.
            if WORKER_HOSTNAME_LABEL not in worker_service_labels:
                raise WorkerNotFound(extra_data={"authority": authority})
            worker_frontends_by_authority[authority] = WorkerFrontend.model_validate(
                worker_service_labels
            )
        return worker_frontends_by_authority

    async def _applied_revisions_by_authority(
        self, authorities: Collection[IngressAuthority]
    ) -> dict[IngressAuthority, dict[IngressFrontendKey, AppliedIngressRevision]]:
        applied_revisions_of_authorities = await asyncio.gather(
            *(self._read_applied_revisions_of_authority(authority) for authority in authorities)
        )
        return dict(zip(authorities, applied_revisions_of_authorities, strict=True))

    async def _read_applied_revisions_of_authority(
        self, authority: IngressAuthority
    ) -> dict[IngressFrontendKey, AppliedIngressRevision]:
        async with self._etcd_call_limit:
            try:
                applied_revision_subtrees_by_frontend_key = await self._etcd.get_prefix(
                    self._authority_applied_revisions_etcd_prefix(authority)
                )
            except EtcdClientError as e:
                raise TraefikEtcdRequestFailedError(
                    str(e), extra_data={"authority": authority}
                ) from e
        return {
            IngressFrontendKey(frontend_key): AppliedIngressRevision.model_validate(
                applied_revision_subtree
            )
            for frontend_key, applied_revision_subtree in applied_revision_subtrees_by_frontend_key.items()
        }

    def _authority_applied_revisions_etcd_prefix(self, authority: IngressAuthority) -> str:
        return f"{_APPLIED_INGRESS_REVISIONS_ETCD_PREFIX}/worker_{authority}/"

    def _applied_revision_etcd_key(self, ingress_key: IngressKey) -> str:
        authority_prefix = self._authority_applied_revisions_etcd_prefix(ingress_key.authority)
        return f"{authority_prefix}{ingress_key.frontend_key}/revision"
