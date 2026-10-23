from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final, override

from ai.backend.appproxy.common.defs import (
    WORKER_AUTHORITY_LABEL,
    WORKER_HOSTNAME_LABEL,
    WORKER_SERVICE_GROUP,
    WORKER_TLS_LISTEN_LABEL,
    WORKER_WILDCARD_DOMAIN_LABEL,
)
from ai.backend.appproxy.common.errors.service import WorkerNotFound
from ai.backend.appproxy.common.etcd import TraefikEtcd, convert_to_etcd_dict
from ai.backend.appproxy.coordinator.clients.worker.base import BaseWorkerClient
from ai.backend.appproxy.coordinator.clients.worker.traefik_routing_config import (
    TraefikRoutingConfigFactory,
)
from ai.backend.appproxy.coordinator.errors.ingress import (
    TraefikIngressConcurrentWriteError,
    TraefikIngressRevisionConflictError,
)
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAuthority,
    IngressKey,
)
from ai.backend.common.etcd import NestedStrKeyedMapping
from ai.backend.common.service_discovery.service_discovery import ServiceDiscovery

# Outside every worker_{authority} root key, so Traefik never reads it.
_REVISION_ROOT: Final[str] = "ingress_revisions"


@dataclass(frozen=True)
class TraefikWorkerClientArgs:
    etcd: TraefikEtcd
    worker_service_discovery: ServiceDiscovery
    routing_config_factory: TraefikRoutingConfigFactory


class TraefikWorkerClient(BaseWorkerClient):
    """Writes each ingress to Traefik etcd as one set of subtrees, replaced by the same or a newer
    revision. The revision is kept in etcd and guards the replacement transaction; a write that
    another write to the same frontend beats fails instead of retrying."""

    _etcd: TraefikEtcd
    _worker_service_discovery: ServiceDiscovery
    _routing_config_factory: TraefikRoutingConfigFactory

    def __init__(self, args: TraefikWorkerClientArgs) -> None:
        self._etcd = args.etcd
        self._worker_service_discovery = args.worker_service_discovery
        self._routing_config_factory = args.routing_config_factory

    @override
    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        """Writes nothing if any ingress is older than the revision etcd holds, as an api-delivery
        worker does. Each ingress is then written in its own transaction to stay within etcd's
        per-transaction operation limit."""
        worker_service_labels_by_authority = await self._worker_service_labels_by_authority({
            ingress.authority for ingress in ingresses
        })
        held_revisions = [
            await self._etcd.get(self._revision_key(ingress.key())) for ingress in ingresses
        ]
        for ingress, held_revision in zip(ingresses, held_revisions, strict=True):
            if held_revision is not None and int(held_revision) > ingress.revision:
                raise TraefikIngressRevisionConflictError(
                    f"frontend {ingress.frontend.key()} holds revision {held_revision}, "
                    f"got {ingress.revision}",
                    extra_data={
                        "authority": ingress.authority,
                        "frontend_key": ingress.frontend.key(),
                    },
                )
        for ingress, held_revision in zip(ingresses, held_revisions, strict=True):
            await self._write(
                ingress, worker_service_labels_by_authority[ingress.authority], held_revision
            )

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        for ingress_key in keys:
            routing_config_etcd_keys = self._routing_config_factory.routing_config_etcd_keys(
                ingress_key
            )
            replacements: dict[str, NestedStrKeyedMapping] = {
                routing_config_etcd_key: {} for routing_config_etcd_key in routing_config_etcd_keys
            }
            replacements[self._revision_prefix(ingress_key)] = {}
            await self._etcd.atomic_replace_prefixes(replacements)

    async def _write(
        self,
        ingress: Ingress,
        worker_service_labels: Mapping[str, str],
        held_revision: str | None,
    ) -> None:
        ingress_key = ingress.key()
        replacements = self._generate_ingress_subtree(ingress, worker_service_labels)
        replacements[self._revision_prefix(ingress_key)] = {"revision": str(ingress.revision)}
        if not await self._etcd.compare_and_replace_prefixes(
            replacements, guards={self._revision_key(ingress_key): held_revision}
        ):
            raise TraefikIngressConcurrentWriteError(
                f"frontend {ingress.frontend.key()} changed after revision {held_revision} "
                "was read",
                extra_data={
                    "authority": ingress.authority,
                    "frontend_key": ingress.frontend.key(),
                },
            )

    async def _worker_service_labels_by_authority(
        self, authorities: Iterable[IngressAuthority]
    ) -> dict[IngressAuthority, Mapping[str, str]]:
        try:
            worker_services = await self._worker_service_discovery.get_service_group(
                WORKER_SERVICE_GROUP
            )
        except ValueError:
            # RedisServiceDiscovery raises ValueError for a group with no registered service.
            worker_services = []
        # A worker that registers no hostname label predates the Traefik labels.
        labels_by_authority = {
            worker_service.labels[WORKER_AUTHORITY_LABEL]: worker_service.labels
            for worker_service in worker_services
            if WORKER_AUTHORITY_LABEL in worker_service.labels
            and WORKER_HOSTNAME_LABEL in worker_service.labels
        }
        worker_service_labels_by_authority: dict[IngressAuthority, Mapping[str, str]] = {}
        for authority in authorities:
            worker_service_labels = labels_by_authority.get(authority)
            if worker_service_labels is None:
                raise WorkerNotFound(extra_data={"authority": authority})
            worker_service_labels_by_authority[authority] = worker_service_labels
        return worker_service_labels_by_authority

    def _revision_prefix(self, ingress_key: IngressKey) -> str:
        return f"{_REVISION_ROOT}/worker_{ingress_key.authority}/{ingress_key.frontend_key}"

    def _revision_key(self, ingress_key: IngressKey) -> str:
        return f"{self._revision_prefix(ingress_key)}/revision"

    def _generate_ingress_subtree(
        self, ingress: Ingress, worker_service_labels: Mapping[str, str]
    ) -> dict[str, NestedStrKeyedMapping]:
        routing_config_factory = self._routing_config_factory
        # Every routing config key of the ingress is listed so a protocol or middleware it no
        # longer has is cleared in the same transaction.
        subtrees: dict[str, NestedStrKeyedMapping] = {
            routing_config_etcd_key: {}
            for routing_config_etcd_key in routing_config_factory.routing_config_etcd_keys(
                ingress.key()
            )
        }
        hostname = worker_service_labels[WORKER_HOSTNAME_LABEL]
        wildcard_domain = worker_service_labels.get(WORKER_WILDCARD_DOMAIN_LABEL)
        tls_listen = worker_service_labels.get(WORKER_TLS_LISTEN_LABEL) == "true"
        routing_configs = routing_config_factory.routing_configs_by_etcd_key(
            ingress, hostname=hostname, wildcard_domain=wildcard_domain, tls_listen=tls_listen
        )
        for routing_config_etcd_key, routing_config in routing_configs.items():
            subtrees[routing_config_etcd_key] = convert_to_etcd_dict(routing_config)
        return subtrees
