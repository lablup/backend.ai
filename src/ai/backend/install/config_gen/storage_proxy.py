"""
Shared Storage Proxy configuration generation.

Used by both TUI dev mode (context.py) and pyinfra deploy scripts
to apply storage proxy config to existing tomlkit documents.
"""

from __future__ import annotations

from dataclasses import dataclass

import tomlkit


@dataclass(frozen=True)
class StorageProxyParams:
    """Parameters for generating storage proxy config."""

    # Etcd
    etcd_host: str = "127.0.0.1"
    etcd_port: int = 8120
    etcd_namespace: str = "local"
    etcd_user: str | None = None
    etcd_password: str | None = None

    # Storage proxy
    secret: str = ""
    ipc_base_path: str = "ipc/storage-proxy"

    # Client-facing API
    client_host: str = "0.0.0.0"
    client_port: int = 6021

    # Manager-facing API
    manager_host: str = "127.0.0.1"
    manager_port: int = 6022
    manager_secret: str = ""

    # Volume
    volume_path: str = "vfolder/local/volume1"


def _make_inline_table(values: dict[str, object]) -> tomlkit.items.InlineTable:
    table = tomlkit.inline_table()
    for k, v in values.items():
        table[k] = v
    return table


def apply_storage_proxy_config(
    doc: tomlkit.TOMLDocument,
    params: StorageProxyParams,
) -> None:
    """
    Apply storage proxy params to an existing tomlkit document.

    Modifies the document in-place, preserving comments and structure.
    """
    # Etcd
    etcd_table = tomlkit.table()
    etcd_table["addr"] = _make_inline_table({"host": params.etcd_host, "port": params.etcd_port})
    etcd_table["namespace"] = params.etcd_namespace
    if params.etcd_user:
        etcd_table["user"] = params.etcd_user
    if params.etcd_password:
        etcd_table["password"] = params.etcd_password
    doc["etcd"] = etcd_table

    # Storage proxy section
    doc["storage-proxy"]["secret"] = params.secret
    doc["storage-proxy"]["ipc-base-path"] = params.ipc_base_path

    # Client-facing API
    doc["api"]["client"]["service-addr"] = _make_inline_table({
        "host": params.client_host,
        "port": params.client_port,
    })

    # Manager-facing API
    doc["api"]["manager"]["service-addr"] = _make_inline_table({
        "host": params.manager_host,
        "port": params.manager_port,
    })
    doc["api"]["manager"]["secret"] = params.manager_secret

    # Volume
    doc["volume"]["volume1"]["path"] = params.volume_path
