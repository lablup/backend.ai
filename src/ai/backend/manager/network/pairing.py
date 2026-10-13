"""Pair cluster-network drivers only with agent backends that implement them."""

from collections.abc import Iterable, Mapping

from ai.backend.common.etcd import AbstractKVStore, ConfigScopes
from ai.backend.common.network.keys import agent_backend_key
from ai.backend.manager.errors.network import NetworkBackendMismatch
from ai.backend.manager.plugin.network import AbstractNetworkManagerPlugin

# Docker keeps the established Swarm overlay unless the operator explicitly selects another driver.
_PREFERRED_DRIVER = "overlay"


def _serves(plugin: AbstractNetworkManagerPlugin | None, backend: str) -> bool:
    """Whether the plugin can network ``backend``; a plugin that declares nothing is not policed."""
    if plugin is None or plugin.compatible_backends is None:
        return True
    return backend in plugin.compatible_backends


async def resolve_driver_for_agents(
    etcd: AbstractKVStore,
    member_agents: Iterable[str],
    *,
    configured_driver: str | None,
    plugins: Mapping[str, AbstractNetworkManagerPlugin],
) -> str | None:
    """Resolve a driver that can serve the members' backend, keeping the configured one if it can.
    Mixed published runtimes fail: a session needs one uniform network fabric."""
    backends: set[str] = set()
    for agent_id in member_agents:
        backend = await etcd.get(agent_backend_key(agent_id), scope=ConfigScopes.GLOBAL)
        if backend is not None:
            backends.add(backend)
    if not backends:
        return configured_driver  # nobody published; keep whatever the operator configured
    if len(backends) > 1:
        raise NetworkBackendMismatch(
            f"the member agents run different container runtimes ({', '.join(sorted(backends))}). "
            "A multi-node session needs one uniform network fabric, and no cluster-network driver "
            "spans both — schedule the session onto agents of a single backend."
        )
    (backend,) = backends
    if configured_driver is not None and _serves(plugins.get(configured_driver), backend):
        return configured_driver
    serving = sorted(
        name
        for name, plugin in plugins.items()
        if plugin.compatible_backends is not None and backend in plugin.compatible_backends
    )
    if _PREFERRED_DRIVER in serving:
        return _PREFERRED_DRIVER
    return serving[0] if serving else configured_driver


async def require_members_can_serve_driver(
    etcd: AbstractKVStore,
    driver: str,
    plugin: AbstractNetworkManagerPlugin,
    member_agents: Iterable[str],
) -> None:
    """Raise NetworkBackendMismatch if a member agent's backend cannot serve ``driver``."""
    compatible = plugin.compatible_backends
    if compatible is None:
        return  # the plugin declares no backends; not ours to police
    for agent_id in member_agents:
        backend = await etcd.get(agent_backend_key(agent_id), scope=ConfigScopes.GLOBAL)
        if backend is None:
            continue  # not published: an agent of a release that publishes none
        if backend not in compatible:
            expected = ", ".join(sorted(compatible))
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' runs the '{backend}' backend, which cannot serve the "
                f"'{driver}' cluster network driver (that driver needs: {expected}). A multi-node "
                "session needs one uniform fabric; select a driver implemented by that agent "
                "backend."
            )
