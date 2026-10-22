from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Final, override

from ai.backend.appproxy.common.defs import PERMIT_COOKIE_NAME
from ai.backend.appproxy.common.etcd import TraefikEtcd, convert_to_etcd_dict
from ai.backend.appproxy.coordinator.clients.worker.base import BaseWorkerClient
from ai.backend.appproxy.coordinator.config import TraefikConfig
from ai.backend.appproxy.coordinator.errors.ingress import (
    TraefikIngressRevisionConflictError,
    TraefikWildcardDomainMissingError,
)
from ai.backend.appproxy.coordinator.repositories.worker import TraefikWorker, WorkerRepository
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressFrontendKind,
    IngressKey,
    IngressProtocol,
)
from ai.backend.common.etcd import NestedStrKeyedMapping

# Outside every worker_{authority} root key, so Traefik never reads it.
_REVISION_ROOT: Final[str] = "ingress_revisions"


class TraefikWorkerClient(BaseWorkerClient):
    """Writes each ingress to Traefik etcd as one set of subtrees, replaced by the same or a newer
    revision. The revision is kept in etcd and guards the replacement transaction."""

    _etcd: TraefikEtcd
    _workers: WorkerRepository
    _traefik_config: TraefikConfig
    _jwt_secret: str
    _permit_hash_secret: str

    def __init__(
        self,
        etcd: TraefikEtcd,
        workers: WorkerRepository,
        traefik_config: TraefikConfig,
        jwt_secret: str,
        permit_hash_secret: str,
    ) -> None:
        self._etcd = etcd
        self._workers = workers
        self._traefik_config = traefik_config
        self._jwt_secret = jwt_secret
        self._permit_hash_secret = permit_hash_secret

    @override
    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        """Writes nothing if any ingress is older than the revision etcd holds, as an api-delivery
        worker does. Each ingress is then written in its own transaction to stay within etcd's
        per-transaction operation limit."""
        workers = {
            authority: await self._workers.get_traefik_worker(authority)
            for authority in {ingress.authority for ingress in ingresses}
        }
        held_revisions = [
            await self._etcd.get(_revision_key(ingress.key())) for ingress in ingresses
        ]
        for ingress, held in zip(ingresses, held_revisions, strict=True):
            _check_not_older(ingress, held)
        for ingress, held in zip(ingresses, held_revisions, strict=True):
            await self._write(ingress, workers[ingress.authority], held)

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        for key in keys:
            replacements: dict[str, NestedStrKeyedMapping] = {
                prefix: {} for prefix in _ingress_prefixes(key)
            }
            replacements[_revision_prefix(key)] = {}
            await self._etcd.atomic_replace_prefixes(replacements)

    async def _write(self, ingress: Ingress, worker: TraefikWorker, held: str | None) -> None:
        key = ingress.key()
        revision_key = _revision_key(key)
        while True:
            replacements = self._subtrees(ingress, worker)
            replacements[_revision_prefix(key)] = {"revision": str(ingress.revision)}
            if await self._etcd.compare_and_replace_prefixes(
                replacements, guards={revision_key: held}
            ):
                return
            held = await self._etcd.get(revision_key)
            _check_not_older(ingress, held)

    def _subtrees(
        self, ingress: Ingress, worker: TraefikWorker
    ) -> dict[str, NestedStrKeyedMapping]:
        key = ingress.key()
        names = _Names(key)
        # Every prefix of the ingress is listed so a protocol or middleware it no longer has
        # is cleared in the same transaction.
        subtrees: dict[str, NestedStrKeyedMapping] = {
            prefix: {} for prefix in _ingress_prefixes(key)
        }
        match ingress.frontend.protocol:
            case IngressProtocol.TCP:
                root = f"worker_{key.authority}/tcp"
                subtrees[f"{root}/routers/{names.router}"] = convert_to_etcd_dict({
                    "rule": _client_ip_rule(ingress),
                    "service": names.service,
                    "entrypoints": [_entrypoint(ingress)],
                })
                subtrees[f"{root}/services/{names.service}"] = convert_to_etcd_dict(
                    _tcp_service(ingress)
                )
            case IngressProtocol.HTTP | IngressProtocol.HTTP2:
                root = f"worker_{key.authority}/http"
                ranges = [str(network) for network in ingress.access.allowed_client_ips]
                middlewares = ["CORSHeaders"]
                if ranges:
                    middlewares.append(names.ip_allowlist)
                middlewares.append(names.auth)
                router: dict[str, Any] = {
                    "rule": self._host_rule(ingress, worker),
                    "service": names.service,
                    "entrypoints": [_entrypoint(ingress)],
                    "middlewares": middlewares,
                }
                if worker.tls_listen:
                    router["tls"] = ""
                subtrees[f"{root}/routers/{names.router}"] = convert_to_etcd_dict(router)
                subtrees[f"{root}/services/{names.service}"] = convert_to_etcd_dict(
                    _http_service(ingress)
                )
                subtrees[f"{root}/middlewares/CORSHeaders"] = convert_to_etcd_dict({
                    "headers": {
                        "accessControlAllowHeaders": "*",
                        "accessControlAllowOriginList": ["*"],
                    },
                })
                if ranges:
                    subtrees[f"{root}/middlewares/{names.ip_allowlist}"] = convert_to_etcd_dict(
                        self._ip_allowlist(ranges)
                    )
                subtrees[f"{root}/middlewares/{names.auth}"] = {
                    "plugin": {
                        "appproxy-traefik-plugin": {
                            # etcd holds strings only, so the ingress travels as one JSON value.
                            "ingress": ingress.model_dump_json(),
                            "jwt_secret": self._jwt_secret,
                            "permit_hash_secret": self._permit_hash_secret,
                            "permit_cookie_name": PERMIT_COOKIE_NAME,
                        },
                    },
                }
        return subtrees

    def _host_rule(self, ingress: Ingress, worker: TraefikWorker) -> str:
        match ingress.frontend.kind:
            case IngressFrontendKind.PORT:
                return f"Host(`{worker.hostname}`)"
            case IngressFrontendKind.WILDCARD:
                if worker.wildcard_domain is None:
                    raise TraefikWildcardDomainMissingError(
                        extra_data={"authority": ingress.authority}
                    )
                return f"Host(`{ingress.frontend.key()}{worker.wildcard_domain}`)"

    def _ip_allowlist(self, ranges: list[str]) -> dict[str, Any]:
        ip_allowlist: dict[str, Any] = {"sourceRange": ranges}
        strategy = self._traefik_config.client_ip_strategy
        if strategy is not None:
            if strategy.depth is not None:
                ip_allowlist["ipStrategy"] = {"depth": strategy.depth}
            elif strategy.excluded_ips:
                ip_allowlist["ipStrategy"] = {
                    "excludedIPs": [str(network) for network in strategy.excluded_ips],
                }
        return {"ipAllowList": ip_allowlist}


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
    http = f"worker_{key.authority}/http"
    tcp = f"worker_{key.authority}/tcp"
    return [
        f"{http}/routers/{names.router}",
        f"{http}/services/{names.service}",
        f"{http}/middlewares/{names.ip_allowlist}",
        f"{http}/middlewares/{names.auth}",
        f"{tcp}/routers/{names.router}",
        f"{tcp}/services/{names.service}",
    ]


def _revision_prefix(key: IngressKey) -> str:
    return f"{_REVISION_ROOT}/worker_{key.authority}/{key.frontend_key}"


def _revision_key(key: IngressKey) -> str:
    return f"{_revision_prefix(key)}/revision"


def _check_not_older(ingress: Ingress, held: str | None) -> None:
    if held is not None and int(held) > ingress.revision:
        raise TraefikIngressRevisionConflictError(
            f"frontend {ingress.frontend.key()} holds revision {held}, got {ingress.revision}",
            extra_data={"authority": ingress.authority, "frontend_key": ingress.frontend.key()},
        )


def _entrypoint(ingress: Ingress) -> str:
    match ingress.frontend.kind:
        case IngressFrontendKind.PORT:
            return f"portproxy_{ingress.frontend.key()}"
        case IngressFrontendKind.WILDCARD:
            return "domainproxy"


def _client_ip_rule(ingress: Ingress) -> str:
    # TCP routers take no middlewares, so the allowlist goes into the match rule.
    ranges = [str(network) for network in ingress.access.allowed_client_ips]
    if not ranges:
        return "ClientIP(`0.0.0.0/0`)"
    return "ClientIP(" + ", ".join(f"`{cidr}`" for cidr in ranges) + ")"


def _http_service(ingress: Ingress) -> dict[str, Any]:
    servers = [
        {"url": f"http://{target.host}:{target.port}/"}
        for group in ingress.backend.target_groups
        if group.weight > 0
        for target in group.targets
    ]
    if not servers:
        return {}
    return {"loadBalancer": {"servers": servers}}


def _tcp_service(ingress: Ingress) -> dict[str, Any]:
    servers = [
        {"address": f"{target.host}:{target.port}"}
        for group in ingress.backend.target_groups
        if group.weight > 0
        for target in group.targets
    ]
    if not servers:
        return {}
    return {"loadBalancer": {"servers": servers}}
