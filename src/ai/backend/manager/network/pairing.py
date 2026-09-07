"""Pair the cluster-network driver against the agent backends that can actually serve it.

A multi-node session's kernels only reach each other if every member agent puts them on the same
fabric. The two fabrics are not interchangeable: 'overlay' is Docker Swarm, which only the docker
backend speaks, and 'cni' is the BEP-1078 stack, which the containerd backend and its rootless
subclass speak. Handing a driver to an agent of the other kind does not fail — the agent falls back
to something node-local and the session comes up with kernels that cannot see each other, with
nothing in the logs to say why. That is what this refuses.

The check is deliberately one-sided: agents publish their backend at startup, and an agent whose
backend is not published yet (an older agent, or one that has not finished starting) is treated as
unknown-but-allowed. Refusing on absence would take out working deployments the moment this shipped.
"""

import json
import logging
import time
from collections.abc import Iterable

from ai.backend.common.etcd import AbstractKVStore, AsyncEtcd, ConfigScopes
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.network.keys import (
    agent_backend_key,
    agent_boot_key,
    agent_caps_key,
)
from ai.backend.common.network.types import OVERLAY_ENCRYPTION_PROFILE, AgentNetworkCaps
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.network import NetworkBackendMismatch

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

#: How long a published capability record is taken as describing the node that is running now.
#: The agent republishes every 60s, so this is many refreshes' worth of slack -- long enough that
#: a slow or briefly disconnected agent is not thrown out, short enough that an advert left by a
#: boot that is over stops being one.
CAPS_FRESH_FOR_SEC = 600.0
#: How far ahead of this manager's clock a published record may be dated before it stops being
#: evidence of anything. Agents and managers do not share a clock, so a little skew is ordinary;
#: a lot of it is a record that no age check can ever expire.
CAPS_CLOCK_SKEW_SEC = 60.0

# Which agent backend can serve which inter-container network driver.
#
# What a backend has to provide for 'cni' is a container's netns by PID: the data plane is a
# device moved into that netns, and a netns does not care which daemon made it. So the list is
# the backends that offer that seam, not the ones anyone has measured. A backend that arrives
# without it is rejected at `_require_members_cni_capable` on its published caps, not here.
DRIVER_COMPATIBLE_BACKENDS: dict[str, frozenset[str]] = {
    "cni": frozenset({"containerd", "docker", "enroot", "singularity"}),
    "overlay": frozenset({"docker"}),
}
# ...and the inverse: the driver an agent backend needs when the operator has not named one it can
# serve. Choosing the container runtime is the operator's decision; the network driver that goes
# with it is not a second, independent choice they should have to get right as well.
#
# Docker is the one backend that can serve two, so it is listed explicitly rather than derived:
# 'overlay' (Swarm) stays its default, because an existing Docker deployment that upgrades into
# this must not have its fabric changed under it. An operator who wants the BEP-1078 one asks for
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


async def require_members_cni_ready(
    etcd: AsyncEtcd, member_agents: Iterable[str]
) -> dict[str, AgentNetworkCaps]:
    """Raise unless every member agent has SAID it can serve this session's data plane.

    Fail-closed, unlike `require_members_overlay_ready`, and the difference is the point. That one
    guards the Swarm overlay, which has deployments older than the capability probe: refusing an
    agent that has published nothing would strand them, and the worst case of letting one through
    is a driver that already worked. This guards the BEP-1078 path, which has no such history --
    an agent that has published nothing has not wired the seam this needs, and today only the
    docker agent publishes at all. Letting it through hands a session descriptor to a node that
    cannot act on it, and the failure surfaces as a session stuck at create.

    An unreadable capability record is refused for the same reason: it is not an advert.

    :return: the record each agent was admitted on, so what the session is built from is what was
        checked. The tunnel endpoint lives in this record AND under a key of its own, and reading
        the second after admitting on the first is how a session gets pre-seeded with an address
        nobody validated.
    """
    admitted: dict[str, AgentNetworkCaps] = {}
    for agent_id in member_agents:
        raw = await etcd.get(agent_caps_key(agent_id), scope=ConfigScopes.GLOBAL)
        if raw is None:
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' has published no network capabilities, so it has not said it"
                " can serve a cluster-network session. The agent publishes these at startup once"
                " its data plane is wired; until it does, this session cannot be placed on it."
            )
        try:
            caps = AgentNetworkCaps.from_etcd_payload(json.loads(raw))
        except (ValueError, TypeError) as e:
            CommonMetricRegistry.instance().network_pool.observe_invalid_record()
            raise NetworkBackendMismatch(
                f"agent '{agent_id}'s published network capabilities cannot be read ({e}), so"
                " they are not an advert that it can serve this session"
            ) from e
        if "vxlan" not in caps.backends:
            reasons = "; ".join(caps.readiness) or "no reason published"
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' does not advertise the 'vxlan' data-plane backend, so a "
                f"multi-node overlay session placed on it cannot come up: {reasons}"
            )
        # An advert is only about the node that is running NOW. The agent refreshes this on a
        # timer, so one that has stopped moving is one whose publisher has stopped -- the agent is
        # gone, or it came back on a runtime that does not publish these at all and left the last
        # one standing. There is no lease on this client to expire it, so the record carries the
        # time it was written and this is the expiry.
        age = time.time() - (caps.updated_at or 0.0)
        # Bounded on BOTH sides. An advert dated in the future is not fresh, it is unusable: a
        # comparison against `now` cannot expire it, and a clock far enough ahead would keep a
        # dead node admitted indefinitely. (NaN and Infinity never reach here -- the decoder
        # refuses them -- but a merely wrong clock does.)
        if caps.updated_at is None or not -CAPS_CLOCK_SKEW_SEC <= age <= CAPS_FRESH_FOR_SEC:
            raise NetworkBackendMismatch(
                f"agent '{agent_id}'s network capabilities are dated {int(age)}s ago (or"
                f" never), outside the window an agent that is running keeps them in"
                f" ({int(CAPS_FRESH_FOR_SEC)}s old at most, {int(CAPS_CLOCK_SKEW_SEC)}s ahead at"
                " most); they are not an advert about the node that is there now"
            )
        # The runtime that WROTE this advert, from the same write, compared against the runtime
        # the agent says it is running now. Merely checking that the writer could serve CNI was
        # not enough: an agent id restarted onto another runtime republishes its backend key
        # immediately and may never publish capabilities at all, so the manager paired the new
        # runtime with the old runtime's advert for as long as that advert stayed fresh.
        running = await etcd.get(agent_backend_key(agent_id), scope=ConfigScopes.GLOBAL)
        if caps.backend is None:
            raise NetworkBackendMismatch(
                f"agent '{agent_id}'s capabilities do not say which backend published them, so"
                " they cannot be attached to the runtime it is running now"
            )
        if running is not None and caps.backend != running:
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' is running the '{running}' backend but its network"
                f" capabilities were published by '{caps.backend}'. The advert is from a boot that"
                " is over; the runtime there now has not said it can serve this session."
            )
        # Which RUN wrote it, not only which runtime. The runtime name cannot see a restart onto
        # the same runtime -- and an agent that comes back and then fails to publish, or has not
        # got there yet, leaves the previous run's advert standing and fresh for as long as the
        # window lasts. The base agent writes this key at every start, before it publishes
        # anything else, so a mismatch is an advert from a run that is over.
        booted = await etcd.get(agent_boot_key(agent_id), scope=ConfigScopes.GLOBAL)
        if booted is not None and caps.boot_id != booted:
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' is on run {booted}, and its network capabilities were"
                f" published by run {caps.boot_id}. The advert is from a boot that is over; this"
                " one has not said it can serve a cluster-network session."
            )
        if caps.backend not in DRIVER_COMPATIBLE_BACKENDS["cni"]:
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' published its capabilities from the '{caps.backend}'"
                " backend, which cannot serve the 'cni' cluster network driver"
            )
        if not caps.vtep_ip:
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' holds no tunnel endpoint, so a vxlan session placed on it is"
                " refused when it arrives. Set container.advertised-host (or bind-host) to a"
                " routable address this host holds."
            )
        admitted[agent_id] = caps
    return admitted


async def require_members_overlay_ready(etcd: AsyncEtcd, member_agents: Iterable[str]) -> None:
    """Raise if a member agent has published that it cannot serve an overlay session.

    The node already knows -- it probes its tooling at startup and says so in its capabilities.
    Without this the answer went nowhere: the session was scheduled anyway and failed on that one
    node at create time, with the reason in a traceback rather than where the placement was
    decided. An agent that has published nothing is allowed through, so this cannot strand a
    deployment whose agents predate the probe.
    """
    for agent_id in member_agents:
        raw = await etcd.get(agent_caps_key(agent_id), scope=ConfigScopes.GLOBAL)
        if raw is None:
            continue  # not published (yet): unknown, but allowed
        try:
            caps = AgentNetworkCaps(**json.loads(raw))
        except (ValueError, TypeError):
            # Still allowed: failing closed here would strand an agent from every overlay session
            # over one corrupt key, which is worse than a session that fails at create with a
            # named reason. But it is not the same as "not published yet" and must not be silent
            # -- something wrote this, and nobody was told.
            CommonMetricRegistry.instance().network_pool.observe_invalid_record()
            log.warning(
                "agent {}'s published network capabilities cannot be read; allowing it into"
                " overlay sessions on the assumption it is capable, but this key needs looking at",
                agent_id,
            )
            continue
        if "vxlan" in caps.backends:
            continue
        reasons = "; ".join(caps.readiness) or "no reason published"
        raise NetworkBackendMismatch(
            f"agent '{agent_id}' does not advertise the 'vxlan' data-plane backend, so a "
            f"multi-node overlay session placed on it cannot come up: {reasons}"
        )


async def members_can_encrypt(etcd: AsyncEtcd, member_agents: Iterable[str]) -> str | None:
    """Why this session's nodes cannot all hold up an encrypted overlay, or None if they can.

    Unlike every other check in this module, silence here is NOT consent. An agent that publishes
    no capabilities, or one whose record does not name `OVERLAY_ENCRYPTION_PROFILE`, is an agent
    from before this contract existed -- and the two ends of an ESP tunnel must agree on all of
    it. One that cannot do ESN cannot decrypt what one that can sends, so the session comes up
    carrying nothing, on the node nobody was looking at.

    That is exactly what a rolling upgrade produces now that encryption is the default rather than
    something an operator turned on node by node. So the answer to "I cannot tell" is to leave
    this session unencrypted and say why, not to encrypt it and find out.
    """
    for agent_id in member_agents:
        raw = await etcd.get(agent_caps_key(agent_id), scope=ConfigScopes.GLOBAL)
        if raw is None:
            return (
                f"agent '{agent_id}' has published no network capabilities, so this manager cannot"
                " tell whether it speaks the overlay encryption profile"
                f" {OVERLAY_ENCRYPTION_PROFILE!r}"
            )
        try:
            caps = AgentNetworkCaps(**json.loads(raw))
        except (ValueError, TypeError):
            return (
                f"agent '{agent_id}' published a capability record this manager cannot read, so"
                " its overlay encryption profile is unknown"
            )
        if OVERLAY_ENCRYPTION_PROFILE not in caps.encryption_profiles:
            return (
                f"agent '{agent_id}' does not speak the overlay encryption profile"
                f" {OVERLAY_ENCRYPTION_PROFILE!r} (it advertises"
                f" {caps.encryption_profiles or 'none'}); an ESP tunnel needs both ends to agree"
                " on all of it, so a session mixing versions comes up and carries nothing"
            )
    return None
