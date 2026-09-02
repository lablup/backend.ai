"""Configuration-related data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai.backend.common.types import ClusterSSHPortMapping


@dataclass
class NetworkSetup:
    """Network configuration for a session."""

    network_name: str | None = None
    network_config: dict[str, Any] = field(default_factory=dict)
    cluster_ssh_port_mapping: ClusterSSHPortMapping | None = None
    session_network_id: str | None = None
    """
    What ``sessions.network_id`` must hold for ``SessionRow.get_network_ref()`` to
    resolve back to ``network_name``. The column is polymorphic: it holds the
    container network name for a network the session owns, and ``networks.id`` for
    one it merely attaches to.
    """
