import asyncio
import os
import shlex
import subprocess
from collections.abc import AsyncGenerator, Sequence


async def run(
    cmdargs: Sequence[str | bytes | os.PathLike],
    *,
    cwd: os.PathLike | None = None,
) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmdargs,
        cwd=cwd,
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


async def spawn_and_watch(
    cmdargs: Sequence[str | bytes | os.PathLike],
    *,
    cwd: os.PathLike | None = None,
    tail_length: int = 50,
) -> AsyncGenerator[bytes, None]:
    last_lines: list[bytes] = []
    proc = await asyncio.create_subprocess_exec(
        *cmdargs,
        cwd=cwd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            if len(last_lines) > tail_length:
                last_lines.pop(0)
            last_lines.append(line)
            yield line.rstrip()
    finally:
        exit_code = await proc.wait()
    if exit_code != 0:
        raise subprocess.CalledProcessError(
            exit_code,
            shlex.join(map(os.fsdecode, cmdargs)),
            output=b"".join(last_lines),
        )
