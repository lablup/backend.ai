from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, override

from ai.backend.appproxy.common.etcd import TraefikEtcd, convert_to_etcd_dict
from ai.backend.appproxy.coordinator.clients.worker.base import BaseWorkerClient
from ai.backend.appproxy.coordinator.clients.worker.traefik_routing_config import (
    TraefikRoutingConfigFactory,
)
from ai.backend.appproxy.coordinator.errors.ingress import (
    TraefikIngressConcurrentWriteError,
    TraefikIngressRevisionConflictError,
)
from ai.backend.appproxy.coordinator.repositories.worker import TraefikWorker, WorkerRepository
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressKey,
    IngressProtocol,
)
from ai.backend.common.etcd import NestedStrKeyedMapping

# Outside every worker_{authority} root key, so Traefik never reads it.
_REVISION_ROOT: Final[str] = "ingress_revisions"


@dataclass(frozen=True)
class TraefikWorkerClientArgs:
    etcd: TraefikEtcd
    worker_repository: WorkerRepository
    routing_config_factory: TraefikRoutingConfigFactory


class TraefikWorkerClient(BaseWorkerClient):
    """Writes each ingress to Traefik etcd as one set of subtrees, replaced by the same or a newer
    revision. The revision is kept in etcd and guards the replacement transaction; a write that
    another write to the same frontend beats fails instead of retrying."""

    _etcd: TraefikEtcd
    _worker_repository: WorkerRepository
    _routing_config_factory: TraefikRoutingConfigFactory

    def __init__(self, args: TraefikWorkerClientArgs) -> None:
        self._etcd = args.etcd
        self._worker_repository = args.worker_repository
        self._routing_config_factory = args.routing_config_factory

    @override
    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        """Writes nothing if any ingress is older than the revision etcd holds, as an api-delivery
        worker does. Each ingress is then written in its own transaction to stay within etcd's
        per-transaction operation limit."""
        traefik_worker_by_authority = {
            authority: await self._worker_repository.get_traefik_worker(authority)
            for authority in {ingress.authority for ingress in ingresses}
        }
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
                ingress, traefik_worker_by_authority[ingress.authority], held_revision
            )

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        for ingress_key in keys:
            replacements: dict[str, NestedStrKeyedMapping] = {
                object_etcd_key: {} for object_etcd_key in _ingress_object_etcd_keys(ingress_key)
            }
            replacements[self._revision_prefix(ingress_key)] = {}
            await self._etcd.atomic_replace_prefixes(replacements)

    async def _write(
        self, ingress: Ingress, worker: TraefikWorker, held_revision: str | None
    ) -> None:
        ingress_key = ingress.key()
        replacements = self._generate_ingress_subtree(ingress, worker)
        replacements[self._revision_prefix(ingress_key)] = {"revision": str(ingress.revision)}
        if not await self._etcd.compare_and_replace_prefixes(
            replacements, guards={self._revision_key(ingress_key): held_revision}
        ):
            raise TraefikIngressConcurrentWriteError(
                f"frontend {ingress.frontend.key()} changed after revision {held_revision} was read",
                extra_data={
                    "authority": ingress.authority,
                    "frontend_key": ingress.frontend.key(),
                },
            )

    def _revision_prefix(self, ingress_key: IngressKey) -> str:
        return f"{_REVISION_ROOT}/worker_{ingress_key.authority}/{ingress_key.frontend_key}"

    def _revision_key(self, ingress_key: IngressKey) -> str:
        return f"{self._revision_prefix(ingress_key)}/revision"

    def _generate_ingress_subtree(
        self, ingress: Ingress, worker: TraefikWorker
    ) -> dict[str, NestedStrKeyedMapping]:
        ingress_key = ingress.key()
        authority = ingress_key.authority
        frontend_protocol = ingress.frontend.protocol
        object_names = _IngressTraefikObjectNames(ingress_key)
        routing_config_factory = self._routing_config_factory
        # Every object key of the ingress is listed so a protocol or middleware it no longer has
        # is cleared in the same transaction.
        subtrees: dict[str, NestedStrKeyedMapping] = {
            object_etcd_key: {} for object_etcd_key in _ingress_object_etcd_keys(ingress_key)
        }
        router_etcd_key = routing_config_factory.router_etcd_key(
            authority, frontend_protocol, object_names.router_name
        )
        service_etcd_key = routing_config_factory.service_etcd_key(
            authority, frontend_protocol, object_names.service_name
        )
        router_rule = routing_config_factory.router_rule(ingress, worker)
        entrypoint_name = routing_config_factory.entrypoint_name(ingress.frontend)
        match frontend_protocol:
            case IngressProtocol.TCP:
                subtrees[router_etcd_key] = convert_to_etcd_dict(
                    routing_config_factory.tcp_router_config(
                        router_rule, object_names.service_name, entrypoint_name
                    )
                )
                subtrees[service_etcd_key] = convert_to_etcd_dict(
                    routing_config_factory.tcp_service_config(ingress.backend)
                )
            case IngressProtocol.HTTP | IngressProtocol.HTTP2:
                has_allowed_client_ips = bool(ingress.access.allowed_client_ips)
                subtrees[router_etcd_key] = convert_to_etcd_dict(
                    routing_config_factory.http_router_config(
                        router_rule,
                        object_names.service_name,
                        entrypoint_name,
                        ip_allowlist_middleware_name=(
                            object_names.ip_allowlist_middleware_name
                            if has_allowed_client_ips
                            else None
                        ),
                        auth_plugin_middleware_name=object_names.auth_plugin_middleware_name,
                        tls=worker.tls_listen,
                    )
                )
                subtrees[service_etcd_key] = convert_to_etcd_dict(
                    routing_config_factory.http_service_config(ingress.backend)
                )
                cors_headers_etcd_key = routing_config_factory.http_middleware_etcd_key(
                    authority, routing_config_factory.CORS_HEADERS_MIDDLEWARE_NAME
                )
                subtrees[cors_headers_etcd_key] = convert_to_etcd_dict(
                    routing_config_factory.cors_headers_middleware_config()
                )
                if has_allowed_client_ips:
                    ip_allowlist_etcd_key = routing_config_factory.http_middleware_etcd_key(
                        authority, object_names.ip_allowlist_middleware_name
                    )
                    subtrees[ip_allowlist_etcd_key] = convert_to_etcd_dict(
                        routing_config_factory.ip_allowlist_middleware_config(ingress.access)
                    )
                auth_plugin_etcd_key = routing_config_factory.http_middleware_etcd_key(
                    authority, object_names.auth_plugin_middleware_name
                )
                subtrees[auth_plugin_etcd_key] = (
                    routing_config_factory.auth_plugin_middleware_config(ingress)
                )
        return subtrees


class _IngressTraefikObjectNames:
    """Traefik object names of one ingress. Frontend keys hold no '_', so no name of one
    ingress is a prefix of another's."""

    router_name: str
    service_name: str
    ip_allowlist_middleware_name: str
    auth_plugin_middleware_name: str

    def __init__(self, ingress_key: IngressKey) -> None:
        name_prefix = f"bai_ingress_{ingress_key.frontend_key}"
        self.router_name = f"{name_prefix}_router"
        self.service_name = f"{name_prefix}_service"
        self.ip_allowlist_middleware_name = f"{name_prefix}_ipallowlist"
        self.auth_plugin_middleware_name = f"{name_prefix}_auth"


def _ingress_object_etcd_keys(ingress_key: IngressKey) -> list[str]:
    authority = ingress_key.authority
    object_names = _IngressTraefikObjectNames(ingress_key)
    return [
        TraefikRoutingConfigFactory.router_etcd_key(
            authority, IngressProtocol.HTTP, object_names.router_name
        ),
        TraefikRoutingConfigFactory.service_etcd_key(
            authority, IngressProtocol.HTTP, object_names.service_name
        ),
        TraefikRoutingConfigFactory.http_middleware_etcd_key(
            authority, object_names.ip_allowlist_middleware_name
        ),
        TraefikRoutingConfigFactory.http_middleware_etcd_key(
            authority, object_names.auth_plugin_middleware_name
        ),
        TraefikRoutingConfigFactory.router_etcd_key(
            authority, IngressProtocol.TCP, object_names.router_name
        ),
        TraefikRoutingConfigFactory.service_etcd_key(
            authority, IngressProtocol.TCP, object_names.service_name
        ),
    ]
