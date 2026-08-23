"""The singularity (apptainer) agent.

``SingularityAgent`` is a thin subclass of
:class:`~ai.backend.agent.containerd.agent.ContainerdAgent`. It overrides exactly one seam —
``_create_runtime()`` — to drive session containers through the apptainer CLI
(:class:`~ai.backend.agent.singularity.runtime.SingularityRuntime`) instead of the containerd gRPC
daemon. Everything else (OCI-spec build, BEP-1062 session networking, scratch, ssh, recovery) is
inherited unchanged, because the runtime boundary (``OciRuntime``) is the only place the runtimes
differ.
"""

from pathlib import Path
from typing import override

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.containerd.runtime.interface import OciRuntime

from .runtime import SingularityRuntime


def create_runtime(local_config: AgentUnifiedConfig) -> SingularityRuntime:
    """The singularity backend's OCI runtime client.

    Module-level so the agent's ``_create_runtime()`` seam and the discovery's
    ``create_oci_runtime()`` (which is what a kernel reaches for when it needs a short-lived
    client of its own, e.g. to commit) build the same thing from the same place.
    """
    root = Path(local_config.agent.var_base_path) / "singularity"
    return SingularityRuntime(
        # Image sandboxes + their sidecars.
        data_path=root / "data",
        # apptainer's own OCI layer cache, used while building a sandbox from docker://.
        cache_path=root / "cache",
        # One overlay (upper/ + work/) per container.
        runtime_path=root / "runtime",
        # Gate dirs and container logs. Kept out of the paths above so a bind source is never
        # hidden inside the container's own mount namespace.
        state_path=root / "state",
        # The work user the kernel-runner drops to. apptainer does not apply the OCI process.user,
        # so surface the configured kernel uid/gid as the fallback.
        kernel_uid=local_config.container.kernel_uid,
        kernel_gid=local_config.container.kernel_gid,
    )


class SingularityAgent(ContainerdAgent):
    @override
    def _create_runtime(self) -> OciRuntime:
        return create_runtime(self.local_config)
