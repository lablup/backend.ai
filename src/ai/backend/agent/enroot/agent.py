"""The enroot agent.

``EnrootAgent`` is a thin subclass of :class:`~ai.backend.agent.containerd.agent.ContainerdAgent`.
It overrides exactly one seam — ``_create_runtime()`` — to drive session containers through the
enroot CLI (:class:`~ai.backend.agent.enroot.runtime.EnrootRuntime`) instead of the containerd
gRPC daemon. Everything else (OCI-spec build, BEP-1062 session networking, scratch, ssh, recovery)
is inherited unchanged, because the runtime boundary (``OciRuntime``) is the only place the two
runtimes differ.
"""

from pathlib import Path
from typing import override

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.containerd.runtime.interface import OciRuntime

from .runtime import EnrootRuntime


def create_runtime(local_config: AgentUnifiedConfig) -> EnrootRuntime:
    """The enroot backend's OCI runtime client.

    Module-level so the agent's ``_create_runtime()`` seam and the discovery's
    ``create_oci_runtime()`` (which is what a kernel reaches for when it needs a short-lived
    client of its own, e.g. to commit) build the same thing from the same place.
    """
    # enroot keeps its squashfs image cache + per-container runtime/data state under the agent's
    # var dir. (A dedicated `container.enroot_*` config key can replace these defaults later; kept
    # derivation-only for the first pass so no config schema change.)
    enroot_root = Path(local_config.agent.var_base_path) / "enroot"
    return EnrootRuntime(
        data_path=enroot_root / "data",
        cache_path=enroot_root / "cache",
        runtime_path=enroot_root / "runtime",
        # gate/log dirs live OUTSIDE the ENROOT_* paths (enroot hides the runtime path inside
        # the container mount ns, so a bind source under it would be invisible).
        state_path=enroot_root / "state",
        # The work user the kernel-runner drops to. enroot (unlike runc) does not apply the OCI
        # process.user, and the base only injects LOCAL_USER_ID for UID_MATCH images, so surface
        # the configured kernel uid/gid as the fallback.
        kernel_uid=local_config.container.kernel_uid,
        kernel_gid=local_config.container.kernel_gid,
        # An unprivileged agent cannot make a cgroup, and neither runtime has a daemon
        # that would; when a privnet is configured the cgroup work goes there too.
        privnet_socket=local_config.agent.network_privnet_socket,
    )


class EnrootAgent(ContainerdAgent):
    @override
    def _create_runtime(self) -> OciRuntime:
        return create_runtime(self.local_config)
