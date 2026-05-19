"""Cilium implementation of the ``NetworkProvider`` abstraction.

Cilium attaches a workload by running its ``cilium-cni`` plugin, which
registers a Cilium endpoint and assigns an address from the cluster pod
CIDR. The CNI exec itself is the shared ``CniInvoker``; this provider only
supplies the Cilium specifics — which conflist to use and provider
preflight.

Nothing cluster-specific is hardcoded: the conflist ``name``, the CNI conf
and bin directories are configuration (``ContainerdNetworkConfig``). A
cluster may name its conflist anything, and ``cilium-cni`` is discovered
from the conflist's ``plugins[].type`` rather than assumed.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from pathlib import Path

from ai.backend.agent.errors.containerd import CniBinaryMissingError
from ai.backend.logging import BraceStyleAdapter

from .base import NetworkAttachment, NetworkProvider
from .cni import (
    DEFAULT_CNI_BIN_DIR,
    DEFAULT_CNI_CONF_DIR,
    DEFAULT_IFNAME,
    CniInvoker,
    load_conflist,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# The cilium-cni plugin binary name; a Cilium conflist references it by
# this value in `plugins[].type`.
_CILIUM_CNI_PLUGIN = "cilium-cni"

# Conventional `name` field of the conflist a default Cilium install
# writes. Overridable — see the module docstring.
DEFAULT_CILIUM_NETWORK_NAME = "cilium"


class CiliumNetworkProvider(NetworkProvider):
    """Attaches containerd workloads to a Cilium network via cilium-cni."""

    def __init__(
        self,
        *,
        network_name: str = DEFAULT_CILIUM_NETWORK_NAME,
        cni_conf_dir: Path = DEFAULT_CNI_CONF_DIR,
        cni_bin_dir: Path = DEFAULT_CNI_BIN_DIR,
    ) -> None:
        self._network_name = network_name
        self._cni_conf_dir = cni_conf_dir
        self._cni_bin_dir = cni_bin_dir
        self._invoker = CniInvoker(bin_dir=cni_bin_dir)

    @property
    def name(self) -> str:
        return "cilium"

    async def preflight(self) -> None:
        """Verify the cilium-cni plugin binary and the named conflist exist."""
        await asyncio.to_thread(self._validate)

    def _validate(self) -> None:
        binary = self._cni_bin_dir / _CILIUM_CNI_PLUGIN
        if not binary.is_file():
            raise CniBinaryMissingError(
                f"cilium-cni plugin not found at {binary}. Install Cilium's CNI "
                "plugin, or correct [container.containerd.network].cni_bin_dir."
            )
        # Raises CniInvocationError if the named conflist is missing/invalid.
        load_conflist(self._network_name, conf_dir=self._cni_conf_dir)

    async def attach(
        self,
        workload_id: str,
        netns_path: str,
        *,
        labels: Mapping[str, str] | None = None,
    ) -> NetworkAttachment:
        """Attach the network namespace to the Cilium network via cilium-cni."""
        conflist = await asyncio.to_thread(
            load_conflist, self._network_name, conf_dir=self._cni_conf_dir
        )
        result = await self._invoker.add(
            conflist,
            container_id=workload_id,
            netns_path=netns_path,
            ifname=DEFAULT_IFNAME,
        )
        attachment = NetworkAttachment.from_cni_result(
            result, netns_path=netns_path, interface=DEFAULT_IFNAME
        )
        log.info(
            "cilium: attached workload {} -> {} (netns {})",
            workload_id,
            attachment.ipv4,
            netns_path,
        )
        return attachment

    async def detach(self, workload_id: str, netns_path: str) -> None:
        """Detach the network namespace from the Cilium network (release the IP)."""
        conflist = await asyncio.to_thread(
            load_conflist, self._network_name, conf_dir=self._cni_conf_dir
        )
        await self._invoker.delete(
            conflist,
            container_id=workload_id,
            netns_path=netns_path,
            ifname=DEFAULT_IFNAME,
        )
        log.info("cilium: detached workload {} (netns {})", workload_id, netns_path)
