import asyncio
import json
import os
from pathlib import Path
from subprocess import CalledProcessError
from typing import AsyncIterator

from ai.backend.storage.utils import fstime2datetime

from ..subproc import run
from ..types import DirEntry, DirEntryType, Stat, TreeUsage
from .rapidfiles import RapidFileToolsFSOpModel


class RapidFileToolsv2FSOpModel(RapidFileToolsFSOpModel):
    async def copy_tree(
        self,
        src_path: Path,
        dst_path: Path,
    ) -> None:
        extra_opts: list[bytes] = []
        if src_path.is_dir():
            extra_opts.append(b"-r")
        if dst_path.is_dir():
            extra_opts.append(b"-T")
        try:
            await run([  # noqa: F821
                b"pcopy",
                *extra_opts,
                b"-p",
                # os.fsencode(src_path / "."),  # TODO: check if "/." is necessary?
                os.fsencode(src_path),
                os.fsencode(dst_path),
            ])
        except CalledProcessError as e:
            raise RuntimeError(f'"pcopy" command failed: {e.stderr}')

    def scan_tree(
        self,
        path: Path,
        *,
        recursive: bool = True,
    ) -> AsyncIterator[DirEntry]:
        raw_target_path = os.fsencode(path)

        async def _aiter() -> AsyncIterator[DirEntry]:
            proc = await asyncio.create_subprocess_exec(
                b"pls",
                b"--jsonlines",
                raw_target_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            assert proc.stdout is not None
            try:
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    line = line.rstrip(b"\n")
                    item = json.loads(line)
                    item_path = Path(item["path"])
                    entry_type = DirEntryType.FILE
                    if item["filetype"] == 40000:
                        entry_type = DirEntryType.DIRECTORY
                    if item["filetype"] == 120000:
                        entry_type = DirEntryType.SYMLINK
                    yield DirEntry(
                        name=item_path.name,
                        path=item_path,
                        type=entry_type,
                        stat=Stat(
                            size=item["size"],
                            owner=str(item["uid"]),
                            mode=item["mode"],
                            modified=fstime2datetime(item["mtime"]),
                            created=fstime2datetime(item["ctime"]),
                        ),
                        symlink_target="",  # TODO: should be tested on PureStorage
                    )
            finally:
                await proc.wait()

        return _aiter()

    async def scan_tree_usage(
        self,
        path: Path,
    ) -> TreeUsage:
        total_size = 0
        total_count = 0
        raw_target_path = os.fsencode(path)
        # Measure the exact file sizes and bytes
        proc = await asyncio.create_subprocess_exec(
            b"pdu",
            b"-0",
            b"-b",
            b"-a",
            raw_target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout is not None
        try:
            # TODO: check slowdowns when there are millions of files
            while True:
                try:
                    line = await proc.stdout.readuntil(b"\0")
                    line = line.rstrip(b"\0")
                except asyncio.IncompleteReadError:
                    break
                size, name = line.split(maxsplit=1)
                if len(name) != len(raw_target_path) and name != raw_target_path:
                    total_size += int(size)
                    total_count += 1
        finally:
            await proc.wait()
        return TreeUsage(file_count=total_count, used_bytes=total_size)
