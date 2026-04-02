"""
Shared AppProxy configuration generation.

Used by both TUI dev mode (context.py) and pyinfra deploy scripts
to generate coordinator and worker config dicts from a common set of parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


def build_coordinator_config(params: CoordinatorParams) -> dict[str, Any]:
    """
    Build appproxy coordinator config dict.

    Returns a nested dict that can be written as TOML.
    """
    config: dict[str, Any] = {
        "db": {
            "type": "postgresql",
            "name": params.db_name,
            "user": params.db_user,
            "password": params.db_password,
            "pool_size": params.db_pool_size,
            "max_overflow": params.db_max_overflow,
            "addr": {"host": params.db_host, "port": params.db_port},
        },
        "redis": {
            "addr": {"host": params.redis_host, "port": params.redis_port},
        },
        "proxy_coordinator": {
            "tls_listen": False,
            "tls_advertised": params.tls_advertised,
            "bind_addr": {"host": params.bind_host, "port": params.bind_port},
            "advertised_addr": {
                "host": params.advertised_host,
                "port": params.advertised_port,
            },
        },
        "secrets": {
            "api_secret": params.api_secret,
            "jwt_secret": params.jwt_secret,
        },
        "permit_hash": {
            "secret": params.permit_hash_secret,
        },
    }

    if params.enable_traefik:
        config["proxy_coordinator"]["enable_traefik"] = True
        config["proxy_coordinator"]["traefik"] = {
            "etcd": {
                "namespace": params.etcd_namespace,
                "addr": {"host": params.etcd_host, "port": params.etcd_port},
            },
        }

    return config


def build_worker_config(params: WorkerParams) -> dict[str, Any]:
    """
    Build appproxy worker config dict.

    Returns a nested dict that can be written as TOML.
    Frontend mode logic (port/wildcard/traefik) is handled here.
    """
    config: dict[str, Any] = {
        "redis": {
            "addr": {"host": params.redis_host, "port": params.redis_port},
        },
        "proxy_worker": {
            "coordinator_endpoint": (
                f"{params.coordinator_scheme}://{params.coordinator_host}:{params.coordinator_port}"
            ),
            "tls_listen": False,
            "tls_advertised": params.tls_advertised,
            "frontend_mode": params.frontend_mode.value,
            "api_bind_addr": {
                "host": params.api_bind_host,
                "port": params.api_bind_port,
            },
            "api_advertised_addr": {
                "host": params.api_advertised_host,
                "port": params.api_advertised_port,
            },
        },
        "secrets": {
            "api_secret": params.api_secret,
            "jwt_secret": params.jwt_secret,
        },
        "permit_hash": {
            "secret": params.permit_hash_secret,
        },
    }

    match params.frontend_mode:
        case FrontendMode.PORT:
            config["proxy_worker"]["port_proxy"] = {
                "bind_host": params.port_proxy_bind_host,
                "advertised_host": params.port_proxy_advertised_host,
                "bind_port_range": [
                    params.port_proxy_range_start,
                    params.port_proxy_range_end,
                ],
            }
        case FrontendMode.WILDCARD:
            if params.wildcard_domain:
                config["proxy_worker"]["wildcard_domain"] = {
                    "domain": params.wildcard_domain,
                    "bind_addr": {
                        "host": params.wildcard_bind_host,
                        "port": params.wildcard_bind_port,
                    },
                    "advertised_port": params.wildcard_advertised_port,
                }
            config["proxy_worker"]["api_advertised_addr"] = {
                "host": params.api_advertised_host,
                "port": params.wildcard_advertised_port,
            }
        case FrontendMode.TRAEFIK:
            config["proxy_worker"]["traefik"] = {
                "api_port": params.traefik_api_port,
                "last_used_time_marker_directory": params.traefik_last_used_dir,
                "etcd": {
                    "namespace": params.traefik_etcd_namespace,
                    "addr": {
                        "host": params.traefik_etcd_host,
                        "port": params.traefik_etcd_port,
                    },
                },
                "port_proxy": {
                    "advertised_host": params.port_proxy_advertised_host,
                    "bind_port_range": [
                        params.port_proxy_range_start,
                        params.port_proxy_range_end,
                    ],
                },
            }

    return config
