import asyncio
import logging
import sys
import tempfile
from asyncio import create_subprocess_exec, subprocess
from collections.abc import Iterable, MutableMapping
from pathlib import Path

from .logging import BraceStyleAdapter

logger = BraceStyleAdapter(logging.getLogger())


async def write_file(
    filename: str,
    body: Iterable[str],
    mode: str = "644",
    append: bool = False,
) -> None:
    open_mode = "w" + ("+" if append else "")
    filepath = Path(filename)

    def _write() -> None:
        with filepath.open(open_mode) as fw:
            fw.writelines(line + "\n" for line in body)
        filepath.chmod(int(mode, 8))

    await asyncio.to_thread(_write)


async def write_tempfile(
    body: Iterable[str],
    mode: str = "644",
) -> str | None:
    def _write() -> str:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".py", delete=False
        ) as config:
            for line in body:
                config.write(line)
        Path(config.name).chmod(int(mode, 8))
        return config.name

    return await asyncio.to_thread(_write)


async def run_command(
    command: Iterable[str],
    echo: bool = False,
) -> MutableMapping[str, str] | None:
    proc = await create_subprocess_exec(
        *(str(piece) for piece in command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if echo:
        sys.stdout.buffer.write(out)
        sys.stdout.flush()
        sys.stderr.buffer.write(err)
        sys.stderr.flush()
    return {"out": out.decode("utf8"), "err": err.decode("utf8")}


async def mkdir(
    path: str,
) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


async def log(
    message: str,
    debug: bool = False,
) -> None:
    message = message.replace("{", "{{").replace("}", "}}")
    if debug:
        logger.debug(message)
    else:
        logger.info(message)
