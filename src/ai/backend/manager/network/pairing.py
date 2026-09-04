"""Pair the cluster-network driver against the agent backends that can actually serve it.

A multi-node session's kernels only reach each other if every member agent puts them on the same
fabric. The two fabrics are not interchangeable: 'overlay' is Docker Swarm, which only the docker
backend speaks, and 'cni' is the BEP-1062 stack, which the containerd backend and its rootless
subclass speak. Handing a driver to an agent of the other kind does not fail — the agent falls back
to something node-local and the session comes up with kernels that cannot see each other, with
nothing in the logs to say why. That is what this refuses.

The check is deliberately one-sided: agents publish their backend at startup, and an agent whose
backend is not published yet (an older agent, or one that has not finished starting) is treated as
unknown-but-allowed. Refusing on absence would take out working deployments the moment this shipped.
"""

from collections.abc import Iterable

from ai.backend.common.etcd import AbstractKVStore, AsyncEtcd, ConfigScopes
from ai.backend.common.network.keys import agent_backend_key
from ai.backend.manager.errors.network import NetworkBackendMismatch

# Which agent backend can serve which inter-container network driver.
# 'enroot' and 'singularity' ride the containerd backend's BEP-1062/CNI stack unchanged (both
# agents subclass ContainerdAgent and override only the container runtime), so they serve 'cni'
# exactly like 'containerd' does.
DRIVER_COMPATIBLE_BACKENDS: dict[str, frozenset[str]] = {
    # 'docker' serves 'cni' as well: the BEP-1062 data plane is a vxlan device moved into the
    # container's netns by PID, and a netns does not care which daemon made it. What used to tie
    # that to containerd was the interface the agent code was written against, not the kernel.
    "cni": frozenset({"containerd", "docker", "enroot", "singularity"}),
    "overlay": frozenset({"docker"}),
}
# ...and the inverse: the driver an agent backend needs when the operator has not named one it can
# serve. Choosing the container runtime is the operator's decision; the network driver that goes
# with it is not a second, independent choice they should have to get right as well.
#
# Docker is the one backend that can serve two, so it is listed explicitly rather than derived:
# 'overlay' (Swarm) stays its default, because an existing Docker deployment that upgrades into
# this must not have its fabric changed under it. An operator who wants the BEP-1062 one asks for
# it by name — see resolve_driver_for_agents.
BACKEND_DRIVER: dict[str, str] = {
    **{
        backend: driver
        for driver, backends in DRIVER_COMPATIBLE_BACKENDS.items()
        for backend in backends
    },
    "docker": "overlay",
}


async def resolve_driver_for_agents(
    etcd: AbstractKVStore, member_agents: Iterable[str], *, configured_driver: str | None
) -> str | None:
    """The driver the member agents' backends actually need, or ``configured_driver`` if unknown.

    The agents' runtime is ground truth: a containerd agent cannot speak Swarm and a docker agent
    cannot speak Swarm, so for most backends there is exactly one right answer and no reason to
    make the operator supply it. Docker is the exception — it can serve either — and there the
    configured driver wins, defaulting to 'overlay' when nothing is configured. ``configured_driver`` stays the fallback for agents that have not published their
    backend (older agents, or ones still starting), so this cannot strand an existing deployment.

    Refuses a mixed cluster outright: a multi-node session needs one fabric, and there is no driver
    that spans both.
    """
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
    if (
        configured_driver in DRIVER_COMPATIBLE_BACKENDS
        and backend in DRIVER_COMPATIBLE_BACKENDS[configured_driver]
    ):
        # The operator named a driver this backend can actually serve: honour it. Only Docker can
        # currently be told something other than its default, and only deliberately.
        return configured_driver
    return BACKEND_DRIVER.get(backend, configured_driver)


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
