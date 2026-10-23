from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, override

from ai.backend.appproxy.common.etcd import TraefikEtcd, convert_to_etcd_dict
from ai.backend.appproxy.coordinator.clients.worker.base import BaseWorkerClient
from ai.backend.appproxy.coordinator.clients.worker.traefik_routing_config import (
    TraefikRoutingConfigFactory,
)
from ai.backend.appproxy.coordinator.errors.ingress import TraefikIngressRevisionConflictError
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
    revision. The revision is kept in etcd and guards the replacement transaction."""

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
        workers = {
            authority: await self._worker_repository.get_traefik_worker(authority)
            for authority in {ingress.authority for ingress in ingresses}
        }
        held_revisions = [
            await self._etcd.get(self._revision_key(ingress.key())) for ingress in ingresses
        ]
        for ingress, held in zip(ingresses, held_revisions, strict=True):
            if held is not None and int(held) > ingress.revision:
                raise TraefikIngressRevisionConflictError(
                    f"frontend {ingress.frontend.key()} holds revision {held}, got {ingress.revision}",
                    extra_data={
                        "authority": ingress.authority,
                        "frontend_key": ingress.frontend.key(),
                    },
                )
        for ingress, held in zip(ingresses, held_revisions, strict=True):
            await self._write(ingress, workers[ingress.authority], held)

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        for key in keys:
            replacements: dict[str, NestedStrKeyedMapping] = {
                prefix: {} for prefix in _ingress_prefixes(key)
            }
            replacements[self._revision_prefix(key)] = {}
            await self._etcd.atomic_replace_prefixes(replacements)

    async def _write(self, ingress: Ingress, worker: TraefikWorker, held: str | None) -> None:
        key = ingress.key()
        revision_key = self._revision_key(key)
        while True:
            replacements = self._generate_ingress_subtree(ingress, worker)
            replacements[self._revision_prefix(key)] = {"revision": str(ingress.revision)}
            if await self._etcd.compare_and_replace_prefixes(
                replacements, guards={revision_key: held}
            ):
                return
            held = await self._etcd.get(revision_key)
            if held is not None and int(held) > ingress.revision:
                raise TraefikIngressRevisionConflictError(
                    f"frontend {ingress.frontend.key()} holds revision {held}, got {ingress.revision}",
                    extra_data={
                        "authority": ingress.authority,
                        "frontend_key": ingress.frontend.key(),
                    },
                )

    def _revision_prefix(self, key: IngressKey) -> str:
        return f"{_REVISION_ROOT}/worker_{key.authority}/{key.frontend_key}"

    def _revision_key(self, key: IngressKey) -> str:
        return f"{self._revision_prefix(key)}/revision"

    def _generate_ingress_subtree(
        self, ingress: Ingress, worker: TraefikWorker
    ) -> dict[str, NestedStrKeyedMapping]:
        key = ingress.key()
        names = _Names(key)
        factory = self._routing_config_factory
        # Every prefix of the ingress is listed so a protocol or middleware it no longer has
        # is cleared in the same transaction.
        subtrees: dict[str, NestedStrKeyedMapping] = {
            prefix: {} for prefix in _ingress_prefixes(key)
        }
        root = factory.etcd_prefix(key.authority, ingress.frontend.protocol)
        rule = factory.router_rule(ingress, worker)
        entrypoint_name = factory.entrypoint_name(ingress.frontend)
        match ingress.frontend.protocol:
            case IngressProtocol.TCP:
                subtrees[f"{root}/routers/{names.router}"] = convert_to_etcd_dict(
                    factory.tcp_router_config(rule, names.service, entrypoint_name)
                )
                subtrees[f"{root}/services/{names.service}"] = convert_to_etcd_dict(
                    factory.tcp_service_config(ingress.backend)
                )
            case IngressProtocol.HTTP | IngressProtocol.HTTP2:
                has_allowed_client_ips = bool(ingress.access.allowed_client_ips)
                subtrees[f"{root}/routers/{names.router}"] = convert_to_etcd_dict(
                    factory.http_router_config(
                        rule,
                        names.service,
                        entrypoint_name,
                        ip_allowlist_middleware_name=(
                            names.ip_allowlist if has_allowed_client_ips else None
                        ),
                        auth_plugin_middleware_name=names.auth,
                        tls=worker.tls_listen,
                    )
                )
                subtrees[f"{root}/services/{names.service}"] = convert_to_etcd_dict(
                    factory.http_service_config(ingress.backend)
                )
                subtrees[f"{root}/middlewares/{factory.CORS_HEADERS_MIDDLEWARE_NAME}"] = (
                    convert_to_etcd_dict(factory.cors_headers_middleware_config())
                )
                if has_allowed_client_ips:
                    subtrees[f"{root}/middlewares/{names.ip_allowlist}"] = convert_to_etcd_dict(
                        factory.ip_allowlist_middleware_config(ingress.access)
                    )
                subtrees[f"{root}/middlewares/{names.auth}"] = (
                    factory.auth_plugin_middleware_config(ingress)
                )
        return subtrees


class _Names:
    """Traefik object names of one ingress. Frontend keys hold no '_', so no name of one
    ingress is a prefix of another's."""

    router: str
    service: str
    ip_allowlist: str
    auth: str

    def __init__(self, key: IngressKey) -> None:
        base = f"bai_ingress_{key.frontend_key}"
        self.router = f"{base}_router"
        self.service = f"{base}_service"
        self.ip_allowlist = f"{base}_ipallowlist"
        self.auth = f"{base}_auth"


def _ingress_prefixes(key: IngressKey) -> list[str]:
    names = _Names(key)
    http = TraefikRoutingConfigFactory.etcd_prefix(key.authority, IngressProtocol.HTTP)
    tcp = TraefikRoutingConfigFactory.etcd_prefix(key.authority, IngressProtocol.TCP)
    return [
        f"{http}/routers/{names.router}",
        f"{http}/services/{names.service}",
        f"{http}/middlewares/{names.ip_allowlist}",
        f"{http}/middlewares/{names.auth}",
        f"{tcp}/routers/{names.router}",
        f"{tcp}/services/{names.service}",
    ]
