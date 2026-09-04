"""Real CNI plugin executor (BEP-1062).

Concrete `CniRunner` that invokes CNI plugin binaries per the CNI spec: the plugin
takes no arguments; the action and container context are passed via ``CNI_*``
environment variables and the network config is written to stdin. On ADD the plugin
returns a result JSON on stdout; a non-zero exit carries an error JSON.

A containerd provisioner obtains the container's network namespace from its task PID
(`netns_path_for_pid`) and drives `agent.network.cni.CniAttacher` with this runner.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CNI_PATH = "/opt/cni/bin"


def netns_path_for_pid(pid: int) -> str:
    """The network-namespace path for a process (e.g. a containerd task's PID)."""
    return f"/proc/{pid}/ns/net"


def resolve_plugin_binary(plugin_type: str, cni_path: str) -> str:
    """Resolve a plugin binary under the colon-separated CNI_PATH; fall back to the
    first directory joined with the type (the executor surfaces ENOENT at exec time)."""
    dirs = [d for d in cni_path.split(os.pathsep) if d]
    for directory in dirs:
        candidate = Path(directory) / plugin_type
        if candidate.exists():
            return str(candidate)
    return str(Path(dirs[0] if dirs else DEFAULT_CNI_PATH) / plugin_type)


def build_cni_env(
    command: str,
    *,
    container_id: str,
    netns: str,
    ifname: str,
    cni_path: str,
) -> dict[str, str]:
    return {
        "CNI_COMMAND": command,
        "CNI_CONTAINERID": container_id,
        "CNI_NETNS": netns,
        "CNI_IFNAME": ifname,
        "CNI_PATH": cni_path,
        "PATH": os.environ.get("PATH", ""),
    }


class CniPluginRunner:
    """Callable CNI runner that execs plugin binaries. Usable as `CniAttacher(runner)`."""

    _cni_path: str

    def __init__(self, *, cni_path: str = DEFAULT_CNI_PATH) -> None:
        self._cni_path = cni_path

    async def __call__(
        self,
        command: str,
        *,
        ifname: str,
        netns: str,
        container_id: str,
        config: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        plugin_type = str(config["type"])
        binary = resolve_plugin_binary(plugin_type, self._cni_path)
        env = build_cni_env(
            command,
            container_id=container_id,
            netns=netns,
            ifname=ifname,
            cni_path=self._cni_path,
        )
        proc = await asyncio.create_subprocess_exec(
            binary,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate(json.dumps(dict(config)).encode())
        if proc.returncode != 0:
            raise CniError.from_output(plugin_type, command, proc.returncode, stdout, stderr)
        if command == "ADD" and stdout.strip():
            result: dict[str, Any] = json.loads(stdout)
            return result
        return None


class CniError(RuntimeError):
    @classmethod
    def from_output(
        cls, plugin_type: str, command: str, returncode: int | None, stdout: bytes, stderr: bytes
    ) -> CniError:
        detail = stdout.decode(errors="replace").strip()
        try:
            parsed = json.loads(detail)
            detail = f"{parsed.get('code')}: {parsed.get('msg')}"
        except (ValueError, AttributeError):
            detail = detail or stderr.decode(errors="replace").strip()
        return cls(f"CNI {command} via '{plugin_type}' failed (rc={returncode}): {detail}")
