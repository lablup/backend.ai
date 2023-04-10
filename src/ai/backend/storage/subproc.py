import asyncio
import os
import shlex
import subprocess
from collections.abc import AsyncGenerator, Sequence


async def spawn_and_watch(
    cmdargs: Sequence[str | bytes],
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
            shlex.join(map(lambda b: b.decode() if isinstance(b, bytes) else b, cmdargs)),
            b"".join(last_lines),
        )
