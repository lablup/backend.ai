"""Pair the cluster-network driver against the agent backends that can actually serve it.

A multi-node session's kernels only reach each other if every member agent puts them on the same
fabric. The two fabrics are not interchangeable: 'overlay' is Docker Swarm, which only the docker
backend speaks, and 'cni' is the BEP-1062 stack, which only the containerd backend speaks. Handing
a driver to an agent of the other kind does not fail — the agent falls back to something node-local
and the session comes up with kernels that cannot see each other, with nothing in the logs to say
why. That is what this refuses.

The check is deliberately one-sided: agents publish their backend at startup, and an agent whose
backend is not published yet (an older agent, or one that has not finished starting) is treated as
unknown-but-allowed. Refusing on absence would take out working deployments the moment this shipped.
"""

from collections.abc import Iterable

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.network.keys import agent_backend_key
from ai.backend.manager.errors.network import NetworkBackendMismatch

# Which agent backend can serve which inter-container network driver.
DRIVER_COMPATIBLE_BACKENDS: dict[str, frozenset[str]] = {
    "cni": frozenset({"containerd"}),
    "overlay": frozenset({"docker"}),
}


async def require_members_can_serve_driver(
    etcd: AsyncEtcd, driver: str, member_agents: Iterable[str]
) -> None:
    """Raise NetworkBackendMismatch if a member agent's backend cannot serve ``driver``."""
    compatible = DRIVER_COMPATIBLE_BACKENDS.get(driver)
    if compatible is None:
        return  # a driver we know nothing about; not ours to police
    for agent_id in member_agents:
        backend = await etcd.get(agent_backend_key(agent_id), scope=ConfigScopes.GLOBAL)
        if backend is None:
            continue  # not published (yet): unknown, but allowed — see the module docstring
        if backend not in compatible:
            expected = ", ".join(sorted(compatible))
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' runs the '{backend}' backend, which cannot serve the "
                f"'{driver}' cluster network driver (that driver needs: {expected}). A multi-node "
                "session needs one uniform fabric: pair the containerd backend with "
                "default_driver='cni', and the docker backend with 'overlay'."
            )
