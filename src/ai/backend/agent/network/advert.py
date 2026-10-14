"""What every agent advertises about its networking, whichever network plugin it runs."""

from __future__ import annotations

from ai.backend.common.etcd import AbstractKVStore, ConfigScopes
from ai.backend.common.network.keys import agent_backend_key, agent_boot_key

__all__ = ("publish_backend",)


async def publish_backend(etcd: AbstractKVStore, agent_id: str, backend: str, boot_id: str) -> None:
    """Publish this run's boot id, then the agent's runtime backend (e.g. ``docker``).

    The boot id goes first: with the backend first, a same-runtime restart briefly re-admits
    whatever the previous run advertised.
    """
    await etcd.put(agent_boot_key(agent_id), boot_id, scope=ConfigScopes.GLOBAL)
    await etcd.put(agent_backend_key(agent_id), backend, scope=ConfigScopes.GLOBAL)
