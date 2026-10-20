from __future__ import annotations

import asyncio
import logging
import os
import shlex
import subprocess
from collections.abc import Sequence
from pathlib import Path

from ai.backend.common.clients.storage_backends.exascaler.exceptions import (
    EXAScalerCommandFailedError,
    EXAScalerCommandStdoutNotAvailableError,
)
from ai.backend.common.dto.clients.storage_backends.exascaler.response import (
    LustreProjectQuota,
    LustreServerConnection,
)
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


def _byte_to_kilobyte(byte: int) -> int:
    return byte // 1024


def _kilobyte_to_byte(kilobyte: int) -> int:
    return kilobyte * 1024


async def _run(cmdargs: Sequence[str | bytes | os.PathLike[str]]) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmdargs,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode is not None and proc.returncode != 0:
        raise subprocess.CalledProcessError(
            proc.returncode,
            shlex.join(map(os.fsdecode, cmdargs)),
            output=out,
            stderr=err,
        )
    return out.decode()


class EXAScalerClient:
    """``lfs`` commands run through this host's Lustre client."""

    async def get_lfs_version(self) -> str:
        return (await _run(["lfs", "--version"])).strip().removeprefix("lfs").strip()

    async def check_servers(self) -> list[LustreServerConnection]:
        """Parses ``lfs check servers`` lines of the form ``<target> <state>.``."""
        output = await _run(["sudo", "-n", "lfs", "check", "servers"])
        servers: list[LustreServerConnection] = []
        for line in output.splitlines():
            parts = line.strip().removesuffix(".").rsplit(maxsplit=1)
            if len(parts) == 2:
                servers.append(LustreServerConnection(name=parts[0], state=parts[1]))
        return servers

    async def set_quota_by_project(self, pid: int, path: Path, limit_bytes: int) -> None:
        quota_limit = _byte_to_kilobyte(limit_bytes)
        try:
            await _run([
                b"sudo",
                b"lfs",
                b"setquota",
                b"-p",
                str(pid),
                f"-B{quota_limit}",
                path,
            ])
        except subprocess.CalledProcessError as e:
            raise EXAScalerCommandFailedError(
                f"'lfs setquota -p {pid}' command failed: {e.stderr}"
            ) from e

    async def unset_quota_by_project(self, pid: int, path: Path) -> None:
        await self.set_quota_by_project(pid, path, 0)

    async def set_project_id(self, pid: int, path: Path) -> None:
        try:
            await _run([
                b"sudo",
                b"lfs",
                b"project",
                b"-p",
                str(pid),
                b"-r",
                b"-s",
                str(path),
            ])
        except subprocess.CalledProcessError as e:
            raise EXAScalerCommandFailedError(
                f"'lfs project -p {pid}' command failed: {e.stderr}"
            ) from e

    async def get_quota_by_project(self, pid: int, qspath: Path) -> LustreProjectQuota | None:
        proc = await asyncio.create_subprocess_exec(
            b"lfs",
            b"quota",
            b"-p",
            str(pid),
            str(qspath),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            if proc.stdout is None:
                raise EXAScalerCommandStdoutNotAvailableError(
                    "lfs quota process stdout is not available"
                )
            next_line_is_quota = False
            line = ""
            while True:
                try:
                    raw = await proc.stdout.readline()
                    if not raw:
                        break
                    line = raw.decode()
                except asyncio.IncompleteReadError:
                    break
                words = line.split()
                if next_line_is_quota:
                    raw_used_bytes, hard_limit = words[0], int(words[2])
                    if hard_limit == 0:
                        return None
                    raw_used_bytes = raw_used_bytes.removesuffix("*")
                    used_bytes = _kilobyte_to_byte(int(raw_used_bytes))
                    limit_bytes = _kilobyte_to_byte(hard_limit)
                    if used_bytes < 0 or limit_bytes < 0:
                        log.warning(
                            "negative quota usage reported",
                            used_bytes=used_bytes,
                            limit_bytes=limit_bytes,
                            report_line=line,
                        )
                    return LustreProjectQuota(used_bytes=used_bytes, limit_bytes=limit_bytes)
                if Path(words[0]) == qspath:
                    next_line_is_quota = True
                    continue
            return None
        finally:
            await proc.wait()
