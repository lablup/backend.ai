from __future__ import annotations

import asyncio
import json
from pathlib import Path, PurePosixPath
from typing import AsyncIterator, FrozenSet, Sequence
from uuid import UUID

from aiotools import aclosing

from ai.backend.common.types import BinarySize, HardwareMetadata

from ..abc import CAP_FAST_SCAN, CAP_METRIC, CAP_VFOLDER
from ..types import (
    DirEntry,
    DirEntryType,
    FSPerfMetric,
    FSUsage,
    Stat,
    VFolderUsage,
)
from ..utils import fstime2datetime
from ..vfs import BaseVolume
from .purity import PurityClient


class FlashBladeVolume(BaseVolume):
    async def init(self) -> None:
        available = True
        try:
            proc = await asyncio.create_subprocess_exec(
                b"pdu",
                b"--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            available = False
        else:
            try:
                stdout, stderr = await proc.communicate()
                if b"RapidFile Toolkit" not in stdout or proc.returncode != 0:
                    available = False
            finally:
                await proc.wait()
        if not available:
            raise RuntimeError(
                "PureStorage RapidFile Toolkit is not installed. "
                "You cannot use the PureStorage backend for the stroage proxy.",
            )
        self.purity_client = PurityClient(
            self.config["purity_endpoint"],
            self.config["purity_api_token"],
            api_version=self.config["purity_api_version"],
        )

    async def shutdown(self) -> None:
        await self.purity_client.aclose()

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset(
            [
                CAP_VFOLDER,
                CAP_METRIC,
                CAP_FAST_SCAN,
            ],
        )

    async def get_hwinfo(self) -> HardwareMetadata:
        async with self.purity_client as client:
            metadata = await client.get_metadata()
        return {
            "status": "healthy",
            "status_info": None,
            "metadata": {
                **metadata,
            },
        }

    async def get_fs_usage(self) -> FSUsage:
        async with self.purity_client as client:
            usage = await client.get_usage(self.config["purity_fs_name"])
        return FSUsage(
            capacity_bytes=usage["capacity_bytes"],
            used_bytes=usage["used_bytes"],
        )

    async def copy_tree(
        self,
        src_vfpath: Path,
        dst_vfpath: Path,
    ) -> None:
        proc = await asyncio.create_subprocess_exec(
            b"pcp",
            b"-r",
            b"-p",
            bytes(src_vfpath / "."),
            bytes(dst_vfpath),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f'"pcp" command failed: {stderr.decode()}')

    async def get_quota(self, vfid: UUID) -> BinarySize:
        raise NotImplementedError

    async def set_quota(self, vfid: UUID, size_bytes: BinarySize) -> None:
        raise NotImplementedError

    async def get_performance_metric(self) -> FSPerfMetric:
        async with self.purity_client as client:
            async with aclosing(
                client.get_nfs_metric(self.config["purity_fs_name"]),
            ) as items:
                async for item in items:
                    return FSPerfMetric(
                        iops_read=item["reads_per_sec"],
                        iops_write=item["writes_per_sec"],
                        io_bytes_read=item["read_bytes_per_sec"],
                        io_bytes_write=item["write_bytes_per_sec"],
                        io_usec_read=item["usec_per_read_op"],
                        io_usec_write=item["usec_per_write_op"],
                    )
                else:
                    raise RuntimeError(
                        "no metric found for the configured flashblade filesystem",
                    )

    async def get_usage(
        self,
        vfid: UUID,
        relpath: PurePosixPath = PurePosixPath("."),
    ) -> VFolderUsage:
        target_path = self.sanitize_vfpath(vfid, relpath)
        total_size = 0
        total_count = 0
        raw_target_path = bytes(target_path)
        # Measure the exact file sizes and bytes
        proc = await asyncio.create_subprocess_exec(
            b"pdu",
            b"-0",
            b"-b",
            b"-a",
            b"-s",
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
        return VFolderUsage(file_count=total_count, used_bytes=total_size)

    async def get_used_bytes(self, vfid: UUID) -> BinarySize:
        vfpath = self.mangle_vfpath(vfid)
        proc = await asyncio.create_subprocess_exec(
            b"pdu",
            b"-hs",
            bytes(vfpath),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"pdu command failed: {stderr.decode()}")
        used_bytes, _ = stdout.decode().split()
        return BinarySize.finite_from_str(used_bytes)

    # ------ vfolder internal operations -------

    def scandir(self, vfid: UUID, relpath: PurePosixPath) -> AsyncIterator[DirEntry]:
        target_path = self.sanitize_vfpath(vfid, relpath)
        raw_target_path = bytes(target_path)

        async def _aiter() -> AsyncIterator[DirEntry]:
            proc = await asyncio.create_subprocess_exec(
                b"pls",
                b"--json",
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
                            # The integer represents the octal number in decimal
                            # (e.g., 644 which actually means 0o644)
                            mode=int(str(item["mode"]), 8),
                            modified=fstime2datetime(item["mtime"]),
                            created=fstime2datetime(item["ctime"]),
                        ),
                        symlink_target="",  # TODO: should be tested on PureStorage
                    )
            finally:
                await proc.wait()

        return _aiter()

    async def copy_file(
        self,
        vfid: UUID,
        src: PurePosixPath,
        dst: PurePosixPath,
    ) -> None:
        src_path = self.sanitize_vfpath(vfid, src)
        dst_path = self.sanitize_vfpath(vfid, dst)
        proc = await asyncio.create_subprocess_exec(
            b"pcp",
            b"-p",
            bytes(src_path),
            bytes(dst_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f'"pcp" command failed: {stderr.decode()}')

    async def delete_files(
        self,
        vfid: UUID,
        relpaths: Sequence[PurePosixPath],
        recursive: bool = False,
    ) -> None:
        target_paths = [bytes(self.sanitize_vfpath(vfid, p)) for p in relpaths]
        proc = await asyncio.create_subprocess_exec(
            b"prm",
            b"-r",
            *target_paths,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError("'prm' command returned a non-zero exit code.")
