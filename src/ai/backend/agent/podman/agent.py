"""The podman agent.

``PodmanAgent`` is a thin subclass of :class:`~ai.backend.agent.containerd.agent.ContainerdAgent`.
It overrides exactly one seam — ``_create_runtime()`` — to drive session containers through the
podman CLI (:class:`~ai.backend.agent.podman.runtime.PodmanRuntime`) instead of the containerd
gRPC daemon. Everything else (OCI-spec build, BEP-1062 session networking, scratch, ssh, recovery)
is inherited unchanged, because the runtime boundary (``OciRuntime``) is the only place the two
runtimes differ.
"""

from pathlib import Path
from typing import override

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.containerd.runtime.interface import OciRuntime

from .runtime import PodmanRuntime


def create_runtime(local_config: AgentUnifiedConfig) -> PodmanRuntime:
    """The podman backend's OCI runtime client.

    Module-level so the agent's ``_create_runtime()`` seam and the discovery's
    ``create_oci_runtime()`` (which is what a kernel reaches for when it needs a short-lived
    client of its own, e.g. to commit) build the same thing from the same place.
    """
    podman_root = Path(local_config.agent.var_base_path) / "podman"
    return PodmanRuntime(
        # podman's image store and per-container runtime state, kept off the invoking user's home.
        data_path=podman_root / "data",
        cache_path=podman_root / "cache",
        runtime_path=podman_root / "runtime",
        # The gate directory is bind-mounted into the container, so it must live outside anything
        # podman may hide inside the container's own mount namespace.
        state_path=podman_root / "state",
        # The work user the kernel-runner drops to. podman is launched as this uid, which is what
        # makes it install a rootless user namespace whose root is the scratch owner.
        kernel_uid=local_config.container.kernel_uid,
        kernel_gid=local_config.container.kernel_gid,
        # Rootless podman cannot place a container in the agent's own cgroup hierarchy; that work
        # goes to the privnet. See PodmanRuntime._confine.
        privnet_socket=local_config.agent.network_privnet_socket,
        # How the operator describes a registry that is not plain public HTTPS (private CA,
        # self-signed, plain HTTP, mirror) — the same `certs.d` tree the containerd backend hands
        # to its transfer service.
        registry_hosts_dir=Path(local_config.container.registry_hosts_dir),
    )


class PodmanAgent(ContainerdAgent):
    @override
    def _create_runtime(self) -> OciRuntime:
        return create_runtime(self.local_config)
