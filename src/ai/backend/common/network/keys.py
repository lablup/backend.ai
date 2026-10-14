"""The etcd keys the agent and the manager core share about cluster networking.

A network plugin keeps its own keys under ``network/``; these are the ones core itself reads.
"""

from __future__ import annotations

__all__ = (
    "agent_backend_key",
    "agent_boot_key",
)


def agent_boot_key(agent_id: str) -> str:
    """Which run of the agent is current; written at every start before anything else it advertises.

    Lets a reader tell this run's adverts from ones an earlier run left behind.
    """
    return f"network/agent/{agent_id}/boot"


def agent_backend_key(agent_id: str) -> str:
    """The agent's container runtime backend, for the manager's driver/backend pairing."""
    return f"network/agent/{agent_id}/backend"
