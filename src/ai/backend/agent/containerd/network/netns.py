"""Per-workload network namespace lifecycle.

The containerd agent owns a network namespace per kernel: it creates the
netns, hands its path to a ``NetworkProvider`` for CNI attachment, and
references it from the container's OCI spec. Owning the netns separately
from the container keeps teardown ordering explicit and lets the address
outlive a container restart.

Named network namespaces are created under ``/run/netns`` — the location
``ip netns`` and CNI plugins resolve them from — so a plugin can ``setns``
into one by path.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from ai.backend.agent.errors.containerd import NetnsSetupError

# Named netns live here; `ip netns` and CNI plugins resolve them by path.
NETNS_DIR = Path("/run/netns")


def netns_path(name: str) -> str:
    """Return the filesystem path of the named network namespace ``name``."""
    return str(NETNS_DIR / name)


async def create_netns(name: str) -> str:
    """Create a named network namespace and return its path.

    Uses ``ip netns add``, which creates a fresh netns and persistently
    bind-mounts it at ``/run/netns/<name>`` — the form CNI plugins expect.
    Requires the agent to run with sufficient privilege (CAP_SYS_ADMIN).
    """
    returncode, stderr = await _run("ip", "netns", "add", name)
    if returncode != 0:
        raise NetnsSetupError(f"Failed to create network namespace '{name}': {stderr}")
    return netns_path(name)


async def delete_netns(name: str) -> None:
    """Delete a named network namespace; a missing namespace is ignored."""
    if not (NETNS_DIR / name).exists():
        return
    returncode, stderr = await _run("ip", "netns", "delete", name)
    if returncode != 0:
        raise NetnsSetupError(f"Failed to delete network namespace '{name}': {stderr}")


async def _run(*argv: str) -> tuple[int, str]:
    """Run a command, returning (returncode, stderr-text)."""
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    return proc.returncode or 0, stderr.decode(errors="replace").strip()
