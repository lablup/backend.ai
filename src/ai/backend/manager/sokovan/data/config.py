"""Configuration-related data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ai.backend.common.types import AgentSelectionStrategy, ClusterSSHPortMapping


@dataclass
class SchedulingConfig:
    """Configuration needed for scheduling decisions."""

    max_container_count_per_agent: Optional[int]
    enforce_spreading_endpoint_replica: bool


@dataclass
class ScalingGroupInfo:
    """Scaling group configuration for scheduling."""

    scheduler_name: str
    agent_selection_strategy: AgentSelectionStrategy


@dataclass
class NetworkSetup:
    """Network configuration for a session."""

    network_name: Optional[str] = None
    network_config: dict[str, Any] = field(default_factory=dict)
    cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None
