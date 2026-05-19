"""Pluggable network-provider abstraction for the containerd backend.

A ``NetworkProvider`` attaches a containerd workload's network namespace
to a cluster network. The generic CNI mechanics — netns lifecycle and the
plugin-chain exec — are shared (see ``netns`` and ``cni``); each provider
(Cilium, Calico, bridge, …) adds only what genuinely differs between CNI
implementations: identity/labels, network-policy lifecycle, provider
preflight, and out-of-band APIs. The CNI *exec protocol* itself is
uniform, so it is deliberately not part of this abstraction.
"""

from __future__ import annotations

import abc
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NetworkAttachment:
    """The outcome of attaching a workload to a network."""

    interface: str
    """Name of the interface created inside the netns (e.g. ``eth0``)."""

    ipv4: str | None
    """The assigned IPv4 address without prefix length, if any."""

    mac: str | None
    """The interface MAC address, if the CNI result reported one."""

    netns_path: str
    """Filesystem path of the attached network namespace."""

    cni_result: Mapping[str, Any] = field(default_factory=dict)
    """The raw CNI ADD result, kept for advanced consumers / debugging."""

    @classmethod
    def from_cni_result(
        cls,
        result: Mapping[str, Any],
        *,
        netns_path: str,
        interface: str,
    ) -> NetworkAttachment:
        """Build an attachment from a raw CNI ADD result.

        The CNI result format is uniform across plugins: ``ips`` carries
        the assigned addresses and ``interfaces`` their MACs.
        """
        ipv4: str | None = None
        for ip_entry in result.get("ips", []):
            address = ip_entry.get("address", "")
            # A CNI result may carry both IPv4 and IPv6; take the first v4.
            if address and ":" not in address:
                ipv4 = address.split("/", 1)[0]
                break
        mac: str | None = None
        for iface in result.get("interfaces", []):
            if iface.get("name") == interface and iface.get("mac"):
                mac = str(iface["mac"])
                break
        return cls(
            interface=interface,
            ipv4=ipv4,
            mac=mac,
            netns_path=netns_path,
            cni_result=dict(result),
        )


class NetworkProvider(abc.ABC):
    """Attaches containerd workloads to a cluster network.

    Concrete implementations — ``CiliumNetworkProvider``,
    ``CalicoNetworkProvider``, a single-host ``BridgeNetworkProvider`` —
    share the ``CniInvoker`` for the actual CNI exec. The agent owns the
    per-workload network namespace and hands its path to ``attach``.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Short provider identifier (``cilium``, ``calico``, …)."""

    @abc.abstractmethod
    async def preflight(self) -> None:
        """Validate provider-specific prerequisites at agent startup."""

    @abc.abstractmethod
    async def attach(
        self,
        workload_id: str,
        netns_path: str,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> NetworkAttachment:
        """Attach the network namespace at ``netns_path`` to the network.

        ``labels`` carry the workload's identity (session group, user, …)
        for providers that map them onto network identity. Returns the
        address assignment.
        """

    @abc.abstractmethod
    async def detach(self, workload_id: str, netns_path: str) -> None:
        """Detach a workload's network namespace, releasing its address."""

    async def ensure_isolation(
        self,
        group_id: str,
        member_workload_ids: list[str],
    ) -> None:
        """Apply session-group isolation policy.

        Default is a no-op; providers with a policy engine (Cilium's
        ``CiliumNetworkPolicy``, Calico's ``NetworkPolicy``) override this.
        """
        return

    async def release_isolation(self, group_id: str) -> None:
        """Release a session group's isolation policy. No-op by default."""
        return
