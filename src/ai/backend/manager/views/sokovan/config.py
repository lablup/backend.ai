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
    #: Per-kernel overlay address the manager's central IPAM assigned (BEP-1062), keyed by
    #: kernel id. A launcher-only side channel: it reaches the agent inside each kernel's
    #: creation config, not in the session-wide network config.
    endpoint_ips: dict[str, str] = field(default_factory=dict)
