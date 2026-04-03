"""
Shared Manager configuration generation.

Used by both TUI dev mode (context.py) and pyinfra deploy scripts
to apply manager config to existing tomlkit documents.
"""

from __future__ import annotations

from dataclasses import dataclass

import tomlkit


@dataclass(frozen=True)
class ManagerParams:
    """Parameters for generating manager config."""

    # Etcd
    etcd_port: int = 8120

    # Database
    db_port: int = 8100

    # Manager
    manager_port: int = 8091
    num_proc: int = 1
    ipc_base_path: str = "ipc/manager"


def _make_inline_table(values: dict[str, object]) -> tomlkit.items.InlineTable:
    table = tomlkit.inline_table()
    for k, v in values.items():
        table[k] = v
    return table


def apply_manager_config(
    doc: tomlkit.TOMLDocument,
    params: ManagerParams,
) -> None:
    """
    Apply manager params to an existing tomlkit document.

    Modifies the document in-place, preserving comments and structure.
    """
    # Etcd port
    doc["etcd"]["addr"]["port"] = params.etcd_port

    # Database port
    doc["db"]["addr"]["port"] = params.db_port

    # Manager service
    doc["manager"]["service-addr"]["port"] = params.manager_port
    doc["manager"]["num-proc"] = params.num_proc
    doc["manager"]["ipc-base-path"] = params.ipc_base_path
