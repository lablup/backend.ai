"""Pair cluster-network drivers only with agent backends that implement them.

Missing legacy capability records remain allowed; published incompatible backends fail closed.
"""

import json
import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass

from ai.backend.common.etcd import AbstractKVStore, AsyncEtcd, ConfigScopes
from ai.backend.common.metrics.metric import CommonMetricRegistry
from ai.backend.common.network.keys import (
    agent_backend_key,
    agent_boot_key,
    agent_caps_key,
    agent_ready_key,
)
from ai.backend.common.network.types import OVERLAY_ENCRYPTION_PROFILE, AgentNetworkCaps
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.network import NetworkBackendMismatch

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

#: Maximum age of an agent capability record; agents refresh it every 60 seconds.
CAPS_FRESH_FOR_SEC = 600.0
#: Maximum tolerated clock skew for capability records dated in the future.
CAPS_CLOCK_SKEW_SEC = 60.0

# Keep this list implementation-backed. Docker is currently the only agent discovery that exposes
# a container locator and publishes cluster-network capabilities.
DRIVER_COMPATIBLE_BACKENDS: dict[str, frozenset[str]] = {
    "cni": frozenset({"docker"}),
    "overlay": frozenset({"docker"}),
}
# Docker defaults to the established Swarm overlay unless the operator explicitly selects CNI.
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
    """Resolve a supported driver, preserving the configured value for unknown backends.

    Mixed published runtimes fail because a session requires one uniform network fabric.
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
        # The configured driver is authoritative only when this backend implements it.
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
                "session needs one uniform fabric; select a driver implemented by that agent "
                "backend."
            )


@dataclass(frozen=True)
class AdmittedAgent:
    """One agent's advert, as it stood when the session was admitted on it.

    The raw bytes travel with the decoded record because admission is a read and building the
    session is a long sequence of writes. Carrying what was read lets the last of those writes be
    conditional on it -- so an agent that restarted, or withdrew, while its session was being
    built cannot have that session declared READY over the advert it has already taken back.
    """

    caps: AgentNetworkCaps
    raw: str
    #: What the agent's identity keys held at admission. Not the capability record: that carries a
    #: timestamp the agent rewrites every minute to say it is still there, so a condition on its
    #: bytes would turn a heartbeat into a fence. These move only when the agent restarts or
    #: changes runtime, which is the thing that actually invalidates an admission. ``None`` means
    #: the key was absent, which is a condition too -- one appearing is a restart.
    backend_key: str | None
    boot_key: str | None
    #: What the node said it could serve, at admission. Guarded on for the same reason as the two
    #: above and one more: a withdrawal leaves boot and backend exactly as they were -- an agent
    #: shutting down, losing its tunnel endpoint or failing its probe takes back the capability
    #: without restarting -- so those two alone cannot see it happen.
    ready_key: str


async def require_members_cni_ready(
    etcd: AsyncEtcd, member_agents: Iterable[str]
) -> dict[str, AdmittedAgent]:
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
    admitted: dict[str, AdmittedAgent] = {}
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
        # What the node currently says it can serve, and it must agree with the record just read.
        # The two are separate writes, so a disagreement means the advert is being changed right
        # now -- and admitting on a half-published pair is admitting on nothing.
        ready = await etcd.get(agent_ready_key(agent_id), scope=ConfigScopes.GLOBAL)
        if ready != caps.readiness_digest():
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' has withdrawn from cluster-network work, or is republishing"
                " what it can serve right now; its capabilities and its readiness do not describe"
                " the same node"
            )
        if not caps.vtep_ip:
            raise NetworkBackendMismatch(
                f"agent '{agent_id}' holds no tunnel endpoint, so a vxlan session placed on it is"
                " refused when it arrives. Set container.advertised-host (or bind-host) to a"
                " routable address this host holds."
            )
        admitted[agent_id] = AdmittedAgent(caps, raw, running, booted, ready)
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
