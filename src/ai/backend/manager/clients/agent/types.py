from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPoolSpec:
    """Configuration for AgentClientPool behavior."""

    health_check_interval: float = 30.0  # Health check interval in seconds
    failure_threshold: int = 3  # Number of failures before marking unhealthy
    recovery_timeout: float = 60.0  # Timeout before removing unhealthy connections
