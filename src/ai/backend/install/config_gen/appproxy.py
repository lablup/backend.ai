"""
Shared AppProxy configuration generation.

Used by both TUI dev mode (context.py) and pyinfra deploy scripts
to apply coordinator and worker config to existing tomlkit documents,
preserving comments and structure from sample/halfstack config files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import tomlkit

from ai.backend.install.types import FrontendMode


@dataclass(frozen=True)
class CoordinatorParams:
    """Parameters for generating appproxy coordinator config."""

    # Database
    db_host: str
    db_port: int
    db_user: str = "appproxy"
    db_password: str = "develove"
    db_name: str = "appproxy"
    db_pool_size: int = 8
    db_max_overflow: int = 64

    # Redis
    redis_host: str = "127.0.0.1"
    redis_port: int = 8110

    # Secrets
    api_secret: str = ""
    jwt_secret: str = ""
    permit_hash_secret: str = ""

    # Bind/advertised addresses
    bind_host: str = "0.0.0.0"
    bind_port: int = 10200
    advertised_host: str = "127.0.0.1"
    advertised_port: int = 10200

    # TLS
    tls_advertised: bool = False

    # Traefik integration
    enable_traefik: bool = False
    etcd_host: str = "127.0.0.1"
    etcd_port: int = 8120
    etcd_namespace: str = "backend"


@dataclass(frozen=True)
class WorkerParams:
    """Parameters for generating appproxy worker config."""

    # Redis
    redis_host: str = "127.0.0.1"
    redis_port: int = 8110

    # Coordinator
    coordinator_host: str = "127.0.0.1"
    coordinator_port: int = 10200
    coordinator_scheme: str = "http"

    # API bind/advertised
    api_bind_host: str = "0.0.0.0"
    api_bind_port: int = 10201
    api_advertised_host: str = "127.0.0.1"
    api_advertised_port: int = 10201

    # Secrets (must match coordinator)
    api_secret: str = ""
    jwt_secret: str = ""
    permit_hash_secret: str = ""

    # TLS
    tls_advertised: bool = False

    # Frontend mode
    frontend_mode: FrontendMode = FrontendMode.PORT

    # Port proxy (used in PORT and TRAEFIK modes)
    port_proxy_bind_host: str = "0.0.0.0"
    port_proxy_advertised_host: str = "127.0.0.1"
    port_proxy_range_start: int = 10205
    port_proxy_range_end: int = 10300

    # Wildcard domain (used in WILDCARD mode)
    wildcard_domain: str | None = None
    wildcard_bind_host: str = "0.0.0.0"
    wildcard_bind_port: int = 10250
    wildcard_advertised_port: int = 443

    # Traefik (used in TRAEFIK mode)
    traefik_api_port: int = 18080
    traefik_last_used_dir: str = "./last_used"
    traefik_etcd_host: str = "127.0.0.1"
    traefik_etcd_port: int = 8120
    traefik_etcd_namespace: str = "traefik"


def _make_inline_table(values: dict[str, Any]) -> tomlkit.items.InlineTable:
    """Create a tomlkit inline table from a dict."""
    table = tomlkit.inline_table()
    for k, v in values.items():
        table[k] = v
    return table


def apply_coordinator_config(
    doc: tomlkit.TOMLDocument,
    params: CoordinatorParams,
) -> None:
    """
    Apply coordinator params to an existing tomlkit document.

    Modifies the document in-place, preserving comments and structure.
    """
    # Database
    doc["db"]["type"] = "postgresql"  # type: ignore[index]
    doc["db"]["name"] = params.db_name  # type: ignore[index]
    doc["db"]["user"] = params.db_user  # type: ignore[index]
    doc["db"]["password"] = params.db_password  # type: ignore[index]
    doc["db"]["pool_size"] = params.db_pool_size  # type: ignore[index]
    doc["db"]["max_overflow"] = params.db_max_overflow  # type: ignore[index]
    doc["db"]["addr"]["host"] = params.db_host  # type: ignore[index]
    doc["db"]["addr"]["port"] = params.db_port  # type: ignore[index]

    # Redis
    doc["redis"]["addr"] = _make_inline_table({
        "host": params.redis_host,
        "port": params.redis_port,
    })  # type: ignore[index]

    # Secrets
    doc["secrets"]["api_secret"] = params.api_secret  # type: ignore[index]
    doc["secrets"]["jwt_secret"] = params.jwt_secret  # type: ignore[index]
    doc["permit_hash"]["secret"] = params.permit_hash_secret  # type: ignore[index]

    # Bind/advertised addresses
    doc["proxy_coordinator"]["bind_addr"]["host"] = params.bind_host  # type: ignore[index]
    doc["proxy_coordinator"]["bind_addr"]["port"] = params.bind_port  # type: ignore[index]
    doc["proxy_coordinator"]["advertised_addr"]["host"] = params.advertised_host  # type: ignore[index]
    doc["proxy_coordinator"]["advertised_addr"]["port"] = params.advertised_port  # type: ignore[index]

    # TLS
    if params.tls_advertised:
        doc["proxy_coordinator"]["tls_advertised"] = True  # type: ignore[index]

    # Traefik
    if params.enable_traefik:
        doc["proxy_coordinator"]["enable_traefik"] = True  # type: ignore[index]
        traefik_table = tomlkit.table()
        traefik_etcd_table = tomlkit.table()
        traefik_etcd_table["namespace"] = params.etcd_namespace
        traefik_etcd_table["addr"] = _make_inline_table({
            "host": params.etcd_host,
            "port": params.etcd_port,
        })
        traefik_table["etcd"] = traefik_etcd_table
        doc["proxy_coordinator"]["traefik"] = traefik_table  # type: ignore[index]


def apply_worker_config(
    doc: tomlkit.TOMLDocument,
    params: WorkerParams,
) -> None:
    """
    Apply worker params to an existing tomlkit document.

    Modifies the document in-place, preserving comments and structure.
    Frontend mode logic (port/wildcard/traefik) is handled here.
    """
    # Redis
    doc["redis"]["addr"] = _make_inline_table({
        "host": params.redis_host,
        "port": params.redis_port,
    })  # type: ignore[index]

    # Coordinator endpoint
    doc["proxy_worker"]["coordinator_endpoint"] = (  # type: ignore[index]
        f"{params.coordinator_scheme}://{params.coordinator_host}:{params.coordinator_port}"
    )

    # API bind/advertised addresses
    doc["proxy_worker"]["api_bind_addr"] = _make_inline_table(  # type: ignore[index]
        {"host": params.api_bind_host, "port": params.api_bind_port}
    )
    doc["proxy_worker"]["api_advertised_addr"] = _make_inline_table(  # type: ignore[index]
        {"host": params.api_advertised_host, "port": params.api_advertised_port}
    )

    # Secrets
    doc["secrets"]["api_secret"] = params.api_secret  # type: ignore[index]
    doc["secrets"]["jwt_secret"] = params.jwt_secret  # type: ignore[index]
    doc["permit_hash"]["secret"] = params.permit_hash_secret  # type: ignore[index]

    # TLS
    if params.tls_advertised:
        doc["proxy_worker"]["tls_advertised"] = True  # type: ignore[index]

    # Frontend mode
    doc["proxy_worker"]["frontend_mode"] = params.frontend_mode.value  # type: ignore[index]

    # Configure based on frontend_mode
    match params.frontend_mode:
        case FrontendMode.PORT:
            doc["proxy_worker"]["port_proxy"]["advertised_host"] = params.port_proxy_advertised_host  # type: ignore[index]
        case FrontendMode.WILDCARD:
            # Remove port_proxy section
            if "port_proxy" in doc["proxy_worker"]:  # type: ignore[operator]
                del doc["proxy_worker"]["port_proxy"]  # type: ignore[union-attr]

            # Override api_advertised_addr
            doc["proxy_worker"]["api_advertised_addr"] = _make_inline_table(  # type: ignore[index]
                {"host": params.api_advertised_host, "port": params.wildcard_advertised_port}
            )

            # Add wildcard_domain section
            if params.wildcard_domain:
                wildcard_table = tomlkit.table()
                wildcard_table["domain"] = params.wildcard_domain
                wildcard_table["bind_addr"] = _make_inline_table({
                    "host": params.wildcard_bind_host,
                    "port": params.wildcard_bind_port,
                })
                wildcard_table["advertised_port"] = params.wildcard_advertised_port
                doc["proxy_worker"]["wildcard_domain"] = wildcard_table  # type: ignore[index]
        case FrontendMode.TRAEFIK:
            # Remove port_proxy section
            if "port_proxy" in doc["proxy_worker"]:  # type: ignore[operator]
                del doc["proxy_worker"]["port_proxy"]  # type: ignore[union-attr]

            # Add traefik section
            traefik_table = tomlkit.table()
            traefik_table["api_port"] = params.traefik_api_port
            traefik_table["last_used_time_marker_directory"] = params.traefik_last_used_dir
            traefik_etcd_table = tomlkit.table()
            traefik_etcd_table["namespace"] = params.traefik_etcd_namespace
            traefik_etcd_table["addr"] = _make_inline_table({
                "host": params.traefik_etcd_host,
                "port": params.traefik_etcd_port,
            })
            traefik_table["etcd"] = traefik_etcd_table
            port_proxy_table = tomlkit.table()
            port_proxy_table["advertised_host"] = params.port_proxy_advertised_host
            port_proxy_table["bind_port_range"] = [
                params.port_proxy_range_start,
                params.port_proxy_range_end,
            ]
            traefik_table["port_proxy"] = port_proxy_table
            doc["proxy_worker"]["traefik"] = traefik_table  # type: ignore[index]
