"""
Shared Agent configuration generation.

Used by both TUI dev mode (context.py) and pyinfra deploy scripts
to apply agent config to existing tomlkit documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import tomlkit


@dataclass(frozen=True)
class AgentParams:
    """Parameters for generating agent config."""

    # Etcd
    etcd_port: int = 8120

    # Agent RPC
    rpc_port: int = 6001

    # Watcher
    watcher_port: int = 6009

    # Paths
    ipc_base_path: str = "/tmp/backend.ai/ipc"
    var_base_path: str = "./var/lib/backend.ai"
    mount_path: str = "./vfroot/local"

    # Accelerator plugins
    compute_plugins: list[str] = field(default_factory=list)


def _make_inline_table(values: dict[str, object]) -> tomlkit.items.InlineTable:
    table = tomlkit.inline_table()
    for k, v in values.items():
        table[k] = v
    return table


def apply_agent_config(
    doc: tomlkit.TOMLDocument,
    params: AgentParams,
) -> None:
    """
    Apply agent params to an existing tomlkit document.

    Modifies the document in-place, preserving comments and structure.
    """
    # Etcd port
    doc["etcd"]["addr"]["port"] = params.etcd_port

    # Agent RPC
    doc["agent"]["rpc-listen-addr"] = _make_inline_table({
        "host": "127.0.0.1",
        "port": params.rpc_port,
    })

    # Paths
    doc["agent"]["ipc-base-path"] = params.ipc_base_path
    doc["agent"]["var-base-path"] = params.var_base_path
    doc["agent"]["mount-path"] = params.mount_path

    # Accelerator plugins
    if params.compute_plugins:
        doc["agent"]["allow-compute-plugins"] = params.compute_plugins

    # Watcher port
    doc["watcher"]["service-addr"] = _make_inline_table({
        "host": "127.0.0.1",
        "port": params.watcher_port,
    })
