"""nerdctl-based ContainerdRuntimeClient (BEP-1055, initial implementation).

Drives containerd through the ``nerdctl`` CLI with ``--network none`` so nerdctl never
touches networking — CNI ownership stays with the BEP-1055 network subsystem. This is
the first working, end-to-end-verifiable implementation; it can be swapped for a
low-level containerd-gRPC client later without touching the orchestrator or the network
layer (both depend only on the ``ContainerdRuntimeClient`` ABC).

Commands are run via an injectable async runner so the argv construction and output
parsing are unit-testable without a live containerd.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any

from ai.backend.agent.containerd.runtime import ContainerdRuntimeClient, TaskHandle
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# runner(argv) -> (returncode, stdout, stderr)
CommandRunner = Callable[[Sequence[str]], Awaitable[tuple[int, str, str]]]


async def default_command_runner(argv: Sequence[str]) -> tuple[int, str, str]:
    """Run a command via a subprocess and return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode or 0, stdout.decode(errors="replace"), stderr.decode(errors="replace")


class NerdctlError(RuntimeError):
    pass


class NerdctlRuntimeClient(ContainerdRuntimeClient):
    _runner: CommandRunner
    _nerdctl: str
    _namespace: str

    def __init__(
        self,
        runner: CommandRunner,
        *,
        nerdctl_path: str = "nerdctl",
        namespace: str = "backend-ai",
    ) -> None:
        self._runner = runner
        self._nerdctl = nerdctl_path
        self._namespace = namespace

    def _base(self) -> list[str]:
        return [self._nerdctl, "--namespace", self._namespace]

    async def _run(self, args: Sequence[str], *, ok_codes: tuple[int, ...] = (0,)) -> str:
        argv = [*self._base(), *args]
        rc, out, err = await self._runner(argv)
        if rc not in ok_codes:
            raise NerdctlError(f"command failed (rc={rc}): {' '.join(argv)}: {err.strip()}")
        return out

    # --- image service ---
    async def image_exists(self, image_ref: str) -> bool:
        rc, _, _ = await self._runner([*self._base(), "image", "inspect", image_ref])
        return rc == 0

    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        args = ["pull"]
        if auth and (user := auth.get("username")) and (pw := auth.get("password")):
            args += ["--creds", f"{user}:{pw}"]
        args.append(image_ref)
        await self._run(args)

    async def list_images(self) -> Sequence[str]:
        out = await self._run(["images", "--format", "{{.Repository}}:{{.Tag}}"])
        return [line.strip() for line in out.splitlines() if line.strip()]

    async def remove_image(self, image_ref: str) -> None:
        await self._run(["rmi", image_ref])

    async def push_image(self, image_ref: str) -> None:
        await self._run(["push", image_ref])

    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        rc, out, _ = await self._runner([
            *self._base(), "image", "inspect", "--format",
            "{{json .Config.Entrypoint}}\t{{json .Config.Cmd}}", image_ref,
        ])
        if rc != 0:
            return None
        entrypoint_raw, _, cmd_raw = out.strip().partition("\t")

        def _parse(text: str) -> list[str] | None:
            try:
                value = json.loads(text)
            except (ValueError, TypeError):
                return None
            return [str(v) for v in value] if isinstance(value, list) and value else None

        return _parse(entrypoint_raw) or _parse(cmd_raw)

    # --- container/task lifecycle ---
    async def create_container(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: Mapping[str, Any],
    ) -> None:
        # --network none: nerdctl leaves the container with an isolated netns (only lo);
        # the BEP-1055 network layer attaches CNI after start.
        args = ["create", "--name", container_id, "--network", "none", image_ref, *command]
        await self._run(args)

    async def start_container(self, container_id: str) -> TaskHandle:
        await self._run(["start", container_id])
        pid = await self.container_pid(container_id)
        if pid is None or pid == 0:
            raise NerdctlError(f"container {container_id} has no PID after start")
        return TaskHandle(container_id=container_id, pid=pid)

    async def kill_container(self, container_id: str, *, signal: int) -> None:
        await self._run(["kill", "--signal", str(signal), container_id], ok_codes=(0, 1))

    async def remove_container(self, container_id: str) -> None:
        await self._run(["rm", "--force", container_id], ok_codes=(0, 1))

    # --- introspection ---
    async def list_containers(self) -> Sequence[str]:
        out = await self._run(["ps", "--all", "--format", "{{.Names}}"])
        return [line.strip() for line in out.splitlines() if line.strip()]

    async def container_pid(self, container_id: str) -> int | None:
        rc, out, _ = await self._runner([
            *self._base(), "inspect", "--format", "{{.State.Pid}}", container_id
        ])
        if rc != 0:
            return None
        text = out.strip()
        if not text:
            return None
        try:
            pid = int(text)
        except ValueError:
            # some nerdctl versions emit JSON for --format on missing fields; be lenient
            try:
                pid = int(json.loads(text))
            except (ValueError, TypeError):
                return None
        return pid or None

    async def container_status(self, container_id: str) -> str | None:
        rc, out, _ = await self._runner([
            *self._base(), "inspect", "--format", "{{.State.Status}}", container_id
        ])
        if rc != 0:
            return None
        return out.strip() or None
