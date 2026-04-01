"""
Type definitions for Agent client pool.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPoolSpec:
    """Configuration for AgentClientPool."""

    health_check_interval: float
    """Interval in seconds between health checks."""

    failure_threshold: int
    """Number of consecutive failures before marking connection as unhealthy."""

    recovery_timeout: float
    """Time in seconds to wait before removing an unhealthy connection."""
