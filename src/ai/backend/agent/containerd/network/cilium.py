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

# How long to wait for an endpoint to reach 'ready' state before
# PATCHing labels. PATCHing during cilium-cni's k8s-pod reconciliation
# has been observed to race with reserved:init being re-added.
_READY_WAIT_RETRIES = 30
_READY_WAIT_DELAY_SECS = 0.2

# How many times to re-PATCH labels if reserved:init survives.
_LABEL_PATCH_RETRIES = 3
_LABEL_PATCH_RETRY_DELAY_SECS = 0.5


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
        k8s_pod_namespace: str | None = None,
        k8s_pod_name: str | None = None,
    ) -> NetworkAttachment:
        """Attach the network namespace to the Cilium network via cilium-cni.

        ``k8s_pod_namespace`` / ``k8s_pod_name`` are passed to cilium-cni
        as ``CNI_ARGS=K8S_POD_NAMESPACE=...;K8S_POD_NAME=...``; cilium-cni
        records them on the endpoint's ``external-identifiers`` and
        treats the endpoint as orchestration-backed, so it does NOT
        stamp ``reserved:init`` on the security-relevant label set.
        Without these args, even ``user`` labels pushed via the labels
        API leave ``reserved:init`` in the identity's labelset and a
        policy-enforcing fabric drops all traffic (see cni-exp.md
        experiments 7 & 8, and the diagnostics in this commit).

        After CNI ADD, ``labels`` are pushed onto the endpoint's ``user``
        slot via the cilium agent for downstream policy targeting.
        """
        conflist = await asyncio.to_thread(
            load_conflist, self._network_name, conf_dir=self._cni_conf_dir
        )
        cni_args: dict[str, str] | None = None
        if k8s_pod_namespace or k8s_pod_name:
            cni_args = {}
            if k8s_pod_namespace:
                cni_args["K8S_POD_NAMESPACE"] = k8s_pod_namespace
            if k8s_pod_name:
                cni_args["K8S_POD_NAME"] = k8s_pod_name
        result = await self._invoker.add(
            conflist,
            container_id=workload_id,
            netns_path=netns_path,
            ifname=DEFAULT_IFNAME,
            cni_args=cni_args,
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
        # CNI_ARGS aren't needed for DEL — cilium-cni looks up the
        # endpoint by container-id/netns and doesn't re-evaluate
        # orchestration metadata on teardown.
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

        PATCHing the endpoint's user labels mid-regeneration races with
        cilium-cni's k8s-pod reconciler — the reconciler can re-add
        ``reserved:init`` to the security-relevant label set after our
        PATCH lands, leaving the endpoint policy-restricted even though
        the identity number changed. We work around this with a
        three-step dance:

        1. Wait for the endpoint to reach ``state == "ready"`` so the
           reconciler is done with its initial pass.
        2. PATCH ``{user: [<labels>]}``.
        3. Verify the identity labelset no longer carries
           ``reserved:init``; if it does, re-PATCH after a short delay
           up to a few times.
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
            await self._wait_for_endpoint_ready(session, workload_id, endpoint_id)
            user_labels = [f"{_LABEL_SOURCE}:{k}={v}" for k, v in labels.items()]
            for attempt in range(1, _LABEL_PATCH_RETRIES + 1):
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
                # Verify: re-fetch the endpoint and confirm reserved:init
                # is gone from the identity's labelset.
                refreshed = await self._find_endpoint(session, workload_id)
                if refreshed is None:
                    break
                id_labels = (refreshed.get("status") or {}).get("identity", {}).get("labels", [])
                if "reserved:init" not in id_labels:
                    log.info(
                        "cilium: endpoint {} (workload {}) labeled with {} entries "
                        "(stable after {} attempt(s))",
                        endpoint_id,
                        workload_id,
                        len(user_labels),
                        attempt,
                    )
                    return
                log.debug(
                    "cilium: endpoint {} still carries reserved:init after PATCH "
                    "attempt {} — retrying",
                    endpoint_id,
                    attempt,
                )
                await asyncio.sleep(_LABEL_PATCH_RETRY_DELAY_SECS)
            log.warning(
                "cilium: endpoint {} (workload {}) still carries reserved:init "
                "after {} PATCH attempts — policy-enforced traffic may be dropped",
                endpoint_id,
                workload_id,
                _LABEL_PATCH_RETRIES,
            )

    async def _wait_for_endpoint_ready(
        self,
        session: aiohttp.ClientSession,
        workload_id: str,
        endpoint_id: int,
    ) -> None:
        """Poll until the endpoint reports ``state == "ready"`` or we time out."""
        for _ in range(_READY_WAIT_RETRIES):
            ep = await self._find_endpoint(session, workload_id)
            if ep is None:
                break
            state = (ep.get("status") or {}).get("state", "")
            if state == "ready":
                return
            await asyncio.sleep(_READY_WAIT_DELAY_SECS)
        log.debug(
            "cilium: endpoint {} did not reach 'ready' state within "
            "{:.1f}s — proceeding with PATCH anyway",
            endpoint_id,
            _READY_WAIT_RETRIES * _READY_WAIT_DELAY_SECS,
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
