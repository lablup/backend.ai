"""This node's overlay identity, advertised while it can serve (BEP-1079).

Two records under the agent's etcd prefix: its VTEP, which lets the manager pre-seed session
membership, and its capabilities, which is what ADMITS the node to a cluster-network session. Both
say something about the serving state of one process, so they are published when the RPC transport
is up, refreshed on a timer, and withdrawn on the way out. Every backend that takes part in the
data plane publishes the same two records the same way; this is that way, once.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Final

from ai.backend.agent.network.caps import (
    probe_caps,
    publish_caps,
    publish_vtep,
    withdraw_caps,
    withdraw_vtep,
)
from ai.backend.agent.network.session_network import SessionNetwork
from ai.backend.agent.network.vtep import uplink_for_ip, usable_vtep
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.logging import BraceStyleAdapter

__all__ = ("NETWORK_IDENTITY_REFRESH_SEC", "NetworkIdentity")

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

#: How often the published capabilities are re-checked. They answer a question that does not
#: stay answered -- the privileged helper can die long after startup.
NETWORK_IDENTITY_REFRESH_SEC: Final = 60.0


class NetworkIdentity:
    """Publishes, refreshes and withdraws one agent's VTEP and capability records."""

    _etcd: AbstractKVStore
    _agent_id: str
    _backend: str
    _boot_id: str
    _session_network: SessionNetwork
    #: The raw configured address the VTEP was validated from, kept for the diagnostic.
    _host_ip: str
    #: The interface the data plane is BUILT on, half of what this node serves with.
    _serving_uplink: str
    _privnet_socket: str | None
    #: The address peers program into their FDB; None once the host stops holding it.
    _vtep_ip: str | None
    _refresh_task: asyncio.Task[None] | None

    def __init__(
        self,
        etcd: AbstractKVStore,
        *,
        agent_id: str,
        backend: str,
        boot_id: str,
        session_network: SessionNetwork,
        host_ip: str,
        serving_uplink: str,
        privnet_socket: str | None,
        vtep_ip: str | None,
    ) -> None:
        self._etcd = etcd
        self._agent_id = agent_id
        self._backend = backend
        self._boot_id = boot_id
        self._session_network = session_network
        self._host_ip = host_ip
        self._serving_uplink = serving_uplink
        self._privnet_socket = privnet_socket
        self._vtep_ip = vtep_ip
        self._refresh_task = None

    @property
    def vtep_ip(self) -> str | None:
        return self._vtep_ip

    async def start(self) -> None:
        """Publish now, then keep the records honest while the process runs."""
        await self.publish()
        self._refresh_task = asyncio.create_task(self._refresh_forever())

    async def stop(self) -> None:
        """Stop advertising this node, and make sure nothing puts the advert back.

        Three steps, in this order, because two is not enough. Deleting first shuts the door at
        once -- while the advert stands a manager may still place work here, and the freshness
        window would let it for ten minutes after this process is gone. But a refresh already
        running can finish its publish AFTER that delete and put a fresh advert back over a node
        that is shutting down. So the publisher is stopped and waited for, and only then is the
        advert taken away for good.
        """
        for step in ("first", "final"):
            try:
                await withdraw_caps(self._etcd, self._agent_id, self._boot_id)
            except Exception:
                log.exception("could not withdraw this agent's network capabilities ({})", step)
            if step == "first" and self._refresh_task is not None:
                self._refresh_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._refresh_task
                self._refresh_task = None

    async def _refresh_forever(self) -> None:
        while True:
            await asyncio.sleep(NETWORK_IDENTITY_REFRESH_SEC)
            try:
                await self.publish()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("could not refresh this agent's network capabilities")

    async def publish(self) -> None:
        """Advertise this node's overlay identity: its VTEP, then its capabilities.

        What this node advertises is what it can actually SERVE, and that is fixed for the life of
        the process: the session network and the vxlan backend hold the endpoint they were built
        with, and every session already up was built on it. So the host is asked afresh each time
        -- an address can go while this process runs, a link drops, DHCP hands out another -- but
        the answer only ever decides whether to keep advertising, never what to advertise.
        """
        serving = self._session_network.serving_vtep
        live = usable_vtep(self._host_ip)
        # BOTH halves of the serving identity. The same address can move to another NIC and stay
        # perfectly usable, while the vxlan device goes on being created on the interface this
        # process started with -- so the node would probe the new NIC, advertise it healthy, and
        # build the tunnel on the old one.
        uplink = uplink_for_ip(live) if live is not None else None
        intact = live == serving and uplink == self._serving_uplink
        self._vtep_ip = serving if intact else None
        if not intact:
            log.warning(
                "this node's overlay identity has moved (serving {!r} on {!r}, host now holds"
                " {!r} on {!r}); withdrawing from multi-node overlay work until this agent is"
                " restarted",
                serving,
                self._serving_uplink,
                live,
                uplink,
            )
        # The VTEP key first, then the capabilities. The capability record is what ADMITS this
        # node to a session, so it is written last of everything this refresh does.
        if self._vtep_ip is not None:
            await publish_vtep(self._etcd, self._agent_id, self._vtep_ip, self._boot_id)
        else:
            # Retract, not merely skip: the key is durable, so an address published on an earlier
            # boot would otherwise keep being pre-seeded into peers' FDBs long after this node
            # stopped holding it -- by which time it may belong to a different host entirely.
            await withdraw_vtep(self._etcd, self._agent_id, self._boot_id)
            log.warning(
                "no usable VTEP: container.advertised-host/bind-host ({!r}) is not a routable"
                " unicast IPv4 address held by an interface of this host that is up. Single-node"
                " sessions work; a multi-node overlay (vxlan) session scheduled here will be"
                " refused until it is set.",
                self._host_ip,
            )
        # A diagnostic signal for operators (e.g. VXLAN tunnel offload); best-effort, because a
        # failure to describe the uplink must not stop the agent from serving kernels.
        try:
            caps = await probe_caps(
                # The interface sessions are served on, not the one the address is on now.
                self._serving_uplink,
                privnet_socket=self._privnet_socket,
                # Retried here rather than on a loop of its own: this already runs on a timer,
                # and the answer it publishes is exactly what the retry changes.
                recovery_problems=await self._session_network.retry_recovery_fail_close(),
            )
            await publish_caps(
                self._etcd,
                self._agent_id,
                caps,
                backend=self._backend,
                vtep_ip=self._vtep_ip,
                boot_id=self._boot_id,
            )
            for problem in caps.readiness:
                log.warning("overlay readiness: {}", problem)
        except Exception:
            # An advert this node could not renew must not stand: it is what a manager reads to
            # place work here. Withdrawn, not raised: a node that cannot describe its uplink can
            # still serve single-node sessions; with no advert standing it is simply not admitted
            # to a cluster-network session, which is the answer that matters.
            log.exception("could not publish this agent's network capabilities; withdrawing")
            await withdraw_caps(self._etcd, self._agent_id, self._boot_id)
