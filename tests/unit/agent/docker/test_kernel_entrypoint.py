"""The container entrypoint must match what the kernel's mount list can actually provide."""

from pathlib import Path

from ai.backend.agent.docker.agent import _kernel_container_entrypoint
from ai.backend.agent.resources import Mount
from ai.backend.common.types import MountPermission, MountTypes


def _mount(target: str) -> Mount:
    return Mount(
        MountTypes.BIND, Path("/host") / Path(target).name, Path(target), MountPermission.READ_ONLY
    )


def test_launcher_is_used_when_mounted() -> None:
    mounts = [_mount("/opt/kernel/entrypoint.sh"), _mount("/opt/kernel/entrypoint.py")]
    assert _kernel_container_entrypoint(mounts) == [
        "/opt/backend.ai/bin/python",
        "-I",
        "/opt/kernel/entrypoint.py",
    ]


def test_kernel_from_older_agent_keeps_the_shell_script_entrypoint() -> None:
    """A restart replays the persisted mount list, which predates the launcher."""
    mounts = [_mount("/opt/kernel/entrypoint.sh"), _mount("/opt/kernel/fantompass.py")]
    assert _kernel_container_entrypoint(mounts) == ["/opt/kernel/entrypoint.sh"]
