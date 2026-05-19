"""Cilium implementation of the ``NetworkProvider`` abstraction.

Cilium attaches a workload by running its ``cilium-cni`` plugin, which
registers a Cilium endpoint and assigns an address from the cluster pod
CIDR. The CNI exec itself is the shared ``CniInvoker``; this provider
also drives the **node-local cilium agent API** to give a non-k8s
workload a real Cilium identity (so it is not stuck at
``reserved:init`` and dropped by a policy-enforcing fabric — see
``cni-exp.md`` experiments 7 & 8).

Nothing cluster-specific is hardcoded: the conflist ``name``, the CNI
conf/bin directories, and the cilium agent socket path are all
configuration (``ContainerdNetworkConfig``). A cluster may name its
conflist anything, and ``cilium-cni`` is discovered from the
conflist's ``plugins[].type`` rather than assumed.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import aiohttp

from ai.backend.agent.errors.containerd import CiliumIdentityError, CniBinaryMissingError
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

# Default path of the cilium agent's REST API socket on the node.
DEFAULT_CILIUM_AGENT_SOCK = Path("/var/run/cilium/cilium.sock")

# Source prefix attached to user labels we push through the cilium agent
# API. Cilium parses ``<source>:<key>=<value>``; ``container`` is what the
# CNI plugin itself uses for k8s-pod-derived labels, and is the source
# closest to "labels Backend.AI owns".
_LABEL_SOURCE = "container"

# How many times to poll the cilium agent for the endpoint that
# corresponds to our workload right after CNI ADD. cilium-cni registers
# the endpoint synchronously, but the agent's bookkeeping can lag by a
# few hundred ms on a busy node.
_ENDPOINT_LOOKUP_RETRIES = 20

# Delay between endpoint-lookup retries.
_ENDPOINT_LOOKUP_DELAY_SECS = 0.2


class CiliumNetworkProvider(NetworkProvider):
    """Attaches containerd workloads to a Cilium network via cilium-cni.

    After the CNI ADD assigns an IP, the provider talks to the node-local
    cilium agent to push user labels onto the new endpoint. Without
    that step the endpoint stays at ``reserved:init`` identity (because
    a non-k8s workload has no backing Pod for cilium to derive labels
    from) and a policy-enforcing fabric drops its traffic — see
    ``cni-exp.md`` experiments 7 & 8.
    """

    def __init__(
        self,
        *,
        network_name: str = DEFAULT_CILIUM_NETWORK_NAME,
        cni_conf_dir: Path = DEFAULT_CNI_CONF_DIR,
        cni_bin_dir: Path = DEFAULT_CNI_BIN_DIR,
        cilium_agent_sock_path: Path = DEFAULT_CILIUM_AGENT_SOCK,
    ) -> None:
        self._network_name = network_name
        self._cni_conf_dir = cni_conf_dir
        self._cni_bin_dir = cni_bin_dir
        self._cilium_agent_sock_path = cilium_agent_sock_path
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
        """Attach the network namespace to the Cilium network via cilium-cni.

        After CNI ADD, push ``labels`` onto the resulting endpoint via
        the cilium agent so the endpoint exits ``reserved:init`` and
        acquires a real cluster identity. Identity assignment is
        best-effort: a failure is logged but does not abort the attach
        (the agent socket may be unavailable on a non-cilium node, or
        when the workload is intentionally policy-free); cluster-policy
        environments must still treat it as a hard requirement.
        """
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

        if labels:
            try:
                await self._assign_endpoint_identity(workload_id, labels)
            except CiliumIdentityError as e:
                # Surface as a warning rather than rolling the CNI ADD
                # back: on a non-policy fabric the workload is still
                # reachable, and the agent-level rollback would lose the
                # diagnostic context.
                log.warning(
                    "cilium: identity assignment for workload {} failed: {}",
                    workload_id,
                    e,
                )
        return attachment

    async def detach(self, workload_id: str, netns_path: str) -> None:
        """Detach the network namespace from the Cilium network (release the IP).

        The cilium endpoint identity is reference-counted by labels and
        garbage-collected by cilium once no endpoint references it
        anymore, so the CNI DELETE alone is enough — no explicit
        identity teardown is needed (see ``cni-exp.md`` finding 5).
        """
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

    async def _assign_endpoint_identity(
        self,
        workload_id: str,
        labels: Mapping[str, str],
    ) -> None:
        """Push ``labels`` onto the cilium endpoint of ``workload_id``.

        Cilium re-resolves an endpoint's identity from its labelset, so
        a non-empty user labelset on what was a ``reserved:init``
        endpoint pulls the endpoint out of init state into a real
        cluster identity.
        """
        if not self._cilium_agent_sock_path.exists():
            raise CiliumIdentityError(
                f"cilium agent socket not found at {self._cilium_agent_sock_path}; "
                "is the cilium DaemonSet pod running on this node?"
            )
        connector = aiohttp.UnixConnector(path=str(self._cilium_agent_sock_path))
        async with aiohttp.ClientSession(connector=connector) as session:
            endpoint = await self._find_endpoint(session, workload_id)
            if endpoint is None:
                raise CiliumIdentityError(
                    f"no cilium endpoint matches container-id {workload_id!r} "
                    f"after {_ENDPOINT_LOOKUP_RETRIES} retries"
                )
            endpoint_id = endpoint.get("id")
            if endpoint_id is None:
                raise CiliumIdentityError(f"cilium endpoint for {workload_id!r} carries no id")
            user_labels = [f"{_LABEL_SOURCE}:{k}={v}" for k, v in labels.items()]
            try:
                async with session.patch(
                    f"http://localhost/v1/endpoint/{endpoint_id}/labels",
                    json={"user": user_labels},
                ) as resp:
                    if resp.status >= 400:
                        body = await resp.text()
                        raise CiliumIdentityError(
                            f"cilium PATCH endpoint/{endpoint_id}/labels failed "
                            f"({resp.status}): {body.strip()}"
                        )
            except aiohttp.ClientError as e:
                raise CiliumIdentityError(
                    f"cilium PATCH endpoint/{endpoint_id}/labels transport error: {e!r}"
                ) from e
            log.info(
                "cilium: endpoint {} (workload {}) labeled with {} entries",
                endpoint_id,
                workload_id,
                len(user_labels),
            )

    async def _find_endpoint(
        self,
        session: aiohttp.ClientSession,
        workload_id: str,
    ) -> dict[str, Any] | None:
        """Poll the cilium agent for the endpoint carrying ``container-id``."""
        last_error: str | None = None
        for _ in range(_ENDPOINT_LOOKUP_RETRIES):
            try:
                async with session.get("http://localhost/v1/endpoint") as resp:
                    if resp.status >= 400:
                        last_error = (
                            f"GET /v1/endpoint -> {resp.status}: {(await resp.text()).strip()}"
                        )
                    else:
                        endpoints = await resp.json()
                        for ep in endpoints:
                            ext = ep.get("status", {}).get("external-identifiers") or {}
                            if ext.get("container-id") == workload_id:
                                return cast("dict[str, Any]", ep)
                        last_error = (
                            f"no endpoint with container-id={workload_id!r} among {len(endpoints)}"
                        )
            except aiohttp.ClientError as e:
                last_error = f"cilium GET /v1/endpoint transport error: {e!r}"
            await asyncio.sleep(_ENDPOINT_LOOKUP_DELAY_SECS)
        if last_error is not None:
            log.debug("cilium: endpoint lookup gave up after retries: {}", last_error)
        return None
