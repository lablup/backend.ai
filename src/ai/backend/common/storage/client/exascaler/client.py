from __future__ import annotations

import subprocess

from ai.backend.common.storage.client.exascaler.types import (
    EXAScalerClientArgs,
    LustreServerConnection,
)


class EXAScalerClient:
    """Synchronous ``lfs`` commands the backend status check runs."""

    _timeout: float

    def __init__(self, args: EXAScalerClientArgs) -> None:
        self._timeout = args.timeout

    def _run(self, cmd: list[str]) -> str:
        return subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=self._timeout
        ).stdout

    def get_lfs_version(self) -> str:
        return self._run(["lfs", "--version"]).strip().removeprefix("lfs").strip()

    def check_servers(self) -> tuple[LustreServerConnection, ...]:
        """Parses ``lfs check servers`` lines of the form ``<target> <state>.``."""
        output = self._run(["sudo", "-n", "lfs", "check", "servers"])
        servers: list[LustreServerConnection] = []
        for line in output.splitlines():
            parts = line.strip().removesuffix(".").rsplit(maxsplit=1)
            if len(parts) == 2:
                servers.append(LustreServerConnection(name=parts[0], state=parts[1]))
        return tuple(servers)
