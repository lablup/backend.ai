import logging
import os
import sys
import tempfile
from asyncio import create_subprocess_exec, subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Optional

from .logging import BraceStyleAdapter

logger = BraceStyleAdapter(logging.getLogger())


async def write_file(
    variables: Mapping[str, Any],
    filename: str,
    body: Iterable[str],
    mode: str = "644",
    append: bool = False,
) -> None:
    filename = filename.format_map(variables)
    open_mode = "w" + ("+" if append else "")
    with open(filename, open_mode) as fw:
        for line in body:
            fw.write(line.format_map(variables) + "\n")
    os.chmod(filename, int(mode, 8))


async def write_tempfile(
    variables: Mapping[str, Any],
    body: Iterable[str],
    mode: str = "644",
) -> Optional[str]:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".py", delete=False) as config:
        for line in body:
            config.write(line.format_map(variables))
    os.chmod(config.name, int(mode, 8))
    return config.name


async def run_command(
    variables: Mapping[str, Any],
    command: Iterable[str],
    echo=False,
) -> Optional[MutableMapping[str, str]]:
    proc = await create_subprocess_exec(
        *(str(piece).format_map(variables) for piece in command),
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
    variables: Mapping[str, Any],
    path: str,
) -> None:
    Path(path.format_map(variables)).mkdir(parents=True, exist_ok=True)


async def log(
    variables: Mapping[str, Any],
    message: str,
    debug: bool = False,
) -> None:
    message = message.format_map(variables).replace("{", "{{").replace("}", "}}")
    if debug:
        logger.debug(message)
    else:
        logger.info(message)
