"""Agent networking capability probe (BEP-1078).

Each participating agent publishes its networking capabilities under
``network/agent/{id}/caps``. This module detects those capabilities and publishes them.

Key capability: VXLAN tunnel offload. When the NIC/driver reports
``tx-udp_tnl-segmentation: off [fixed]``, VXLAN cannot be hardware-accelerated on
that host — a diagnostic signal for operators sizing the fabric.
"""

from __future__ import annotations

import dataclasses
import json
import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING

from ai.backend.agent.network import command
from ai.backend.agent.network.readiness import Readiness, probe_readiness
from ai.backend.common.etcd import ConfigScopes
from ai.backend.common.network.keys import (
    agent_backend_key,
    agent_caps_key,
    agent_vtep_key,
)
from ai.backend.common.network.types import (
    DEFAULT_VNI_RANGE,
    DEFAULT_VXLAN_PORT,
    OVERLAY_ENCRYPTION_PROFILE,
    AgentNetworkCaps,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.common.etcd import AbstractKVStore

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_TUNNEL_OFFLOAD_FEATURE = "tx-udp_tnl-segmentation"


def parse_tunnel_offload(ethtool_output: str) -> bool:
    """Parse ``ethtool -k <iface>`` output for VXLAN TX tunnel-segmentation offload.

    Returns True only when the feature is explicitly ``on`` (with or without the
    ``[fixed]`` qualifier). ``off`` / ``off [fixed]`` / a missing feature -> False.
    """
    for line in ethtool_output.splitlines():
        line = line.strip()
        if not line.startswith(_TUNNEL_OFFLOAD_FEATURE):
            continue
        _, _, value = line.partition(":")
        return value.strip().split()[0] == "on" if value.strip() else False
    return False


async def _run_ethtool(iface: str) -> str | None:
    """`ethtool -k <iface>`, or None for any reason it did not answer.

    None on a host with no `ethtool` at all, which is an ordinary container image and not an
    error: the caller reads it as "no tunnel offload", which is the safe reading -- the overlay
    works without it. Letting the OSError out took the whole capability probe with it, and with it
    the VXLAN readiness checks that run afterwards.
    """
    try:
        rc, stdout, stderr = await command.run(["ethtool", "-k", iface])
    except FileNotFoundError:
        log.debug("no ethtool on this host; assuming no tunnel offload")
        return None
    except (OSError, command.CommandTimeout) as e:
        log.warning("ethtool -k {} did not answer: {}", iface, e)
        return None
    if rc != 0:
        log.warning(
            "ethtool -k {} failed (rc={}): {}", iface, rc, stderr.decode(errors="replace").strip()
        )
        return None
    return stdout.decode(errors="replace")


def compute_caps(*, tunnel_offload: bool, readiness: Readiness | None = None) -> AgentNetworkCaps:
    """Assemble AgentNetworkCaps from probed facts.

    ``vxlan`` is dropped from the advertised backends when something settled and local would make
    every session here fail -- a missing binary or iptables match. Advertising it anyway is how a
    node that cannot serve the backend still gets handed sessions that fail on it alone.
    """
    findings = readiness or Readiness()
    return AgentNetworkCaps(
        tunnel_offload=tunnel_offload,
        backends=["vxlan"] if findings.can_serve_overlay else [],
        readiness=findings.problems,
        # A separate question from serving the overlay at all. The profile says this node can hold
        # up its end of an ESP tunnel, and advertising it off the back of the generic checks -- ip,
        # bridge, iptables, u32 -- claimed something none of them looked at: a kernel with no XFRM
        # or no AES-GCM passes every one of them and then cannot install a single SA.
        encryption_profiles=([OVERLAY_ENCRYPTION_PROFILE] if findings.can_encrypt_overlay else []),
    )


async def probe_caps(
    iface: str,
    *,
    vxlan_port: int = DEFAULT_VXLAN_PORT,
    vni_range: tuple[int, int] = DEFAULT_VNI_RANGE,
    privnet_socket: str | None = None,
    recovery_problems: Mapping[str, str] | None = None,
) -> AgentNetworkCaps:
    """Probe this host's networking capabilities, and what would stop it serving a session.

    The readiness half is why this is worth more than a boolean: the agent advertised `vxlan`
    unconditionally, so a host with no `xt_u32`, or one whose CNI already owns the overlay's UDP
    port, was handed a session it could only fail -- at create time, on one node, with the reason
    visible in nothing the operator was looking at.
    """
    output = await _run_ethtool(iface)
    tunnel_offload = parse_tunnel_offload(output) if output is not None else False
    readiness = await probe_readiness(
        port=vxlan_port,
        vni_range=vni_range,
        privnet_socket=privnet_socket,
        recovery_problems=recovery_problems,
    )
    return compute_caps(tunnel_offload=tunnel_offload, readiness=readiness)


async def publish_caps(etcd: AbstractKVStore, agent_id: str, caps: AgentNetworkCaps) -> None:
    """Publish this agent's capabilities to etcd for the manager's backend selection."""
    await etcd.put(
        agent_caps_key(agent_id),
        json.dumps(dataclasses.asdict(caps)),
        scope=ConfigScopes.GLOBAL,
    )


async def publish_backend(etcd: AbstractKVStore, agent_id: str, backend: str) -> None:
    """Publish this agent's runtime backend (e.g. 'containerd') so the manager can enforce
    the backend<->network-driver pairing invariant. Called at agent startup."""
    await etcd.put(agent_backend_key(agent_id), backend, scope=ConfigScopes.GLOBAL)


async def publish_vtep(etcd: AbstractKVStore, agent_id: str, vtep_ip: str) -> None:
    """Publish this agent's VTEP (overlay tunnel endpoint = advertised host IP) so the
    manager can pre-seed the per-session membership table at create_network time. That
    removes the peer-publish race: each agent's reconcile-at-start finds every peer's VTEP
    already present instead of waiting for the etcd watch to deliver it. Called at startup."""
    await etcd.put(agent_vtep_key(agent_id), vtep_ip, scope=ConfigScopes.GLOBAL)


async def withdraw_vtep(etcd: AbstractKVStore, agent_id: str) -> None:
    """Retract this agent's VTEP, for a node that no longer has a usable one.

    The key is durable, and the manager pre-seeds member records straight from it — so a node that
    published an address on an earlier boot and now holds none would have its peers program that
    stale address, which by then may belong to a different host entirely. Not publishing is not
    enough; the old value has to go."""
    await etcd.delete(agent_vtep_key(agent_id), scope=ConfigScopes.GLOBAL)
