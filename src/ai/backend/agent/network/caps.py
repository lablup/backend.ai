"""Agent networking capability probe (BEP-1055).

The manager selects a cluster-network data-plane backend per session from each
participating agent's capabilities, published under ``network/agent/{id}/caps``.
This module detects those capabilities and publishes them.

Key capability: VXLAN tunnel offload. When the NIC/driver reports
``tx-udp_tnl-segmentation: off [fixed]``, VXLAN can never be hardware-accelerated
on that host, so the manager should prefer a non-encapsulating backend where the
fabric allows it.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
from typing import TYPE_CHECKING

from ai.backend.common.etcd import ConfigScopes
from ai.backend.common.network.types import AgentNetworkCaps
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
    proc = await asyncio.create_subprocess_exec(
        "ethtool",
        "-k",
        iface,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        log.warning(
            "ethtool -k {} failed (rc={}): {}",
            iface,
            proc.returncode,
            stderr.decode(errors="replace").strip(),
        )
        return None
    return stdout.decode(errors="replace")


def compute_caps(*, tunnel_offload: bool, native_routing_ok: bool) -> AgentNetworkCaps:
    """Assemble AgentNetworkCaps from probed facts.

    ``vxlan`` is always available (the portable default); ``host-gw`` is offered only
    when native routing is known to work on this host's fabric.
    """
    backends = ["vxlan"]
    if native_routing_ok:
        backends.append("host-gw")
    return AgentNetworkCaps(
        tunnel_offload=tunnel_offload,
        native_routing_ok=native_routing_ok,
        backends=backends,
    )


async def probe_caps(iface: str, *, native_routing_ok: bool = False) -> AgentNetworkCaps:
    """Probe this host's networking capabilities.

    ``native_routing_ok`` defaults to False (conservative): a boot-time single-node
    probe cannot confirm that the fabric forwards container-IP frames, so the manager
    falls back to the portable vxlan backend unless native routing is asserted (by
    configuration or a future active two-node probe).
    """
    output = await _run_ethtool(iface)
    tunnel_offload = parse_tunnel_offload(output) if output is not None else False
    return compute_caps(tunnel_offload=tunnel_offload, native_routing_ok=native_routing_ok)


def caps_key(agent_id: str) -> str:
    return f"network/agent/{agent_id}/caps"


async def publish_caps(etcd: AbstractKVStore, agent_id: str, caps: AgentNetworkCaps) -> None:
    """Publish this agent's capabilities to etcd for the manager's backend selection."""
    await etcd.put(
        caps_key(agent_id),
        json.dumps(dataclasses.asdict(caps)),
        scope=ConfigScopes.GLOBAL,
    )
