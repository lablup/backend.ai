"""
Shared Webserver configuration generation.

Used by both TUI dev mode (context.py) and pyinfra deploy scripts
to apply webserver config to existing tomlkit documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import tomlkit


@dataclass(frozen=True)
class WebserverParams:
    """Parameters for generating webserver config."""

    # Manager API
    manager_host: str = "127.0.0.1"
    manager_port: int = 8091

    # Wsproxy
    wsproxy_url: str = ""

    # Endpoint protocol override (e.g., "https")
    force_endpoint_protocol: str | None = None

    # Redis (single mode)
    redis_addr: str | None = None
    # Redis (sentinel mode)
    redis_sentinel: str | None = None
    redis_service_name: str = "mymaster"
    redis_password: str | None = None

    # UI
    menu_blocklist: list[str] = field(default_factory=lambda: ["pipeline"])
    menu_inactivelist: list[str] = field(default_factory=lambda: ["statistics"])


def apply_webserver_config(
    doc: tomlkit.TOMLDocument,
    params: WebserverParams,
) -> None:
    """
    Apply webserver params to an existing tomlkit document.

    Modifies the document in-place, preserving comments and structure.
    """
    # Wsproxy URL (dotted key: service.wsproxy.url)
    if params.wsproxy_url:
        if "wsproxy" in doc["service"]:
            doc["service"]["wsproxy"]["url"] = params.wsproxy_url
        else:
            wsproxy_table = tomlkit.table()
            wsproxy_table["url"] = params.wsproxy_url
            doc["service"]["wsproxy"] = wsproxy_table

    # Endpoint protocol
    if params.force_endpoint_protocol is not None:
        doc["service"]["force_endpoint_protocol"] = params.force_endpoint_protocol

    # Manager API endpoint
    doc["api"]["endpoint"] = f"http://{params.manager_host}:{params.manager_port}"

    # Redis session config
    redis_table = tomlkit.table()
    helper_table = tomlkit.table()
    helper_table["socket_timeout"] = 5.0
    helper_table["socket_connect_timeout"] = 2.0
    helper_table["reconnect_poll_timeout"] = 0.3

    if params.redis_sentinel:
        redis_table["sentinel"] = params.redis_sentinel
        redis_table["service_name"] = params.redis_service_name
    elif params.redis_addr:
        redis_table["addr"] = params.redis_addr

    redis_table["redis_helper_config"] = helper_table
    if params.redis_password:
        redis_table["password"] = params.redis_password
    doc["session"]["redis"] = redis_table

    # UI menus
    doc["ui"]["menu_blocklist"] = ",".join(params.menu_blocklist)
    if params.menu_inactivelist:
        doc["ui"]["menu_inactivelist"] = ",".join(params.menu_inactivelist)
