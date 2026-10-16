from __future__ import annotations

import asyncio
import logging
import os
import re
from collections.abc import AsyncGenerator, AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from stat import S_IFDIR, S_IFLNK
from typing import Any, ClassVar, Final, override

import aiohttp
from yarl import URL

from ai.backend.common.clients.storage_backends.purestorage.exceptions import (
    PureStorageCommandFailedError,
    PureStorageStdoutNotAvailableError,
    RapidFileToolkitVersionNotDetectedError,
    UnauthorizedPurityClient,
)
from ai.backend.common.dto.clients.storage_backends.purestorage.request import (
    PurityListQuery,
)
from ai.backend.common.dto.clients.storage_backends.purestorage.response import (
    PurityArrayMetadata,
    PurityFileSystemUsage,
    PurityNFSMetric,
    RapidFileEntry,
    RapidFileStat,
    RapidFileTreeUsage,
)
from ai.backend.common.dto.clients.storage_backends.purestorage.types import (
    RapidFileEntryType,
)
from ai.backend.common.json import load_json
from ai.backend.common.types import BinarySize
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

FLASHBLADE_TOOLKIT_V2_VERSION_RE: Final = re.compile(r"version p[a-zA-Z\d]+ \(RapidFile\) (2\..+)")
FLASHBLADE_TOOLKIT_V1_VERSION_RE: Final = re.compile(r"p[a-zA-Z\d]+ \(RapidFile Toolkit\) (1\..+)")


@dataclass
class PurityClientArgs:
    endpoint: str
    api_token: str
    api_version: str = "1.8"


class PurityClient:
    """Purity//FB REST API client.

    The caller logs in with ``login()`` and holds ``lock()`` across a login and the calls using it.
    """

    _endpoint: URL
    _api_token: str
    _api_version: str
    _auth_token: str | None
    _lock: asyncio.Lock
    _session: aiohttp.ClientSession

    def __init__(self, args: PurityClientArgs) -> None:
        self._endpoint = URL(args.endpoint)
        self._api_token = args.api_token
        self._api_version = args.api_version
        self._auth_token = None
        self._lock = asyncio.Lock()
        self._session = aiohttp.ClientSession()

    async def aclose(self) -> None:
        await self._session.close()

    @asynccontextmanager
    async def lock(self) -> AsyncIterator[None]:
        async with self._lock:
            yield

    async def login(self) -> None:
        try:
            async with self._session.post(
                self._endpoint / "api" / "login",
                headers={"api-token": self._api_token},
                ssl=False,
                raise_for_status=True,
            ) as resp:
                self._auth_token = resp.headers["x-auth-token"]
                _ = await resp.json()
        except Exception:
            self._auth_token = None
            raise

    def clear_auth_token(self) -> None:
        self._auth_token = None

    def _auth_headers(self) -> dict[str, str]:
        if self._auth_token is None:
            raise UnauthorizedPurityClient("The auth token for Purity API is not initialized.")
        return {"x-auth-token": self._auth_token}

    async def _pages(
        self, path: str, query: PurityListQuery
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Yields each page of a listing, following its continuation token."""
        pagination_token = ""
        while True:
            page_query = query.model_copy(update={"token": pagination_token})
            async with self._session.get(
                self._endpoint / "api" / self._api_version / path,
                headers=self._auth_headers(),
                params=page_query.model_dump(mode="json", by_alias=True, exclude_none=True),
                ssl=False,
                raise_for_status=True,
            ) as resp:
                page: dict[str, Any] = await resp.json()
            yield page
            pagination_token = page["pagination_info"]["continuation_token"]
            if pagination_token is None:
                break

    async def get_metadata(self) -> PurityArrayMetadata | None:
        items = [
            item
            async for page in self._pages("arrays", PurityListQuery())
            for item in page["items"]
        ]
        if not items:
            return None
        first = items[0]
        return PurityArrayMetadata(
            id=first["id"],
            name=first["name"],
            os=first["os"],
            revision=first["revision"],
            version=first["version"],
            blade_count=len(items),
            console_url=str(self._endpoint),
        )

    async def get_nfs_metric(self, fs_name: str) -> AsyncGenerator[PurityNFSMetric, None]:
        async for page in self._pages(
            "file-systems/performance", PurityListQuery(names=fs_name, protocol="NFS")
        ):
            for item in page["items"]:
                yield PurityNFSMetric.model_validate(item)

    async def get_usage(self, fs_name: str) -> PurityFileSystemUsage | None:
        pages = [page async for page in self._pages("file-systems", PurityListQuery(names=fs_name))]
        items = [item for page in pages for item in page["items"]]
        if not items:
            return None
        first = items[0]
        return PurityFileSystemUsage(
            capacity_bytes=pages[-1]["total"]["provisioned"],
            used_bytes=first["space"]["total_physical"],
        )


async def get_toolkit_version() -> int:
    """Returns the installed RapidFile Toolkit major version, or -1 if none is usable."""
    try:
        proc = await asyncio.create_subprocess_exec(
            b"pdu",
            b"--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError:
        return -1
    try:
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            return -1
        version_line = stdout.decode().splitlines()[0]
        if FLASHBLADE_TOOLKIT_V2_VERSION_RE.match(version_line):
            log.info("FlashBlade Toolkit detected", toolkit_version=2)
            return 2
        if FLASHBLADE_TOOLKIT_V1_VERSION_RE.match(version_line):
            log.info("FlashBlade Toolkit detected", toolkit_version=1)
            return 1
        log.warning("unrecognized FlashBlade Toolkit version", version_line=version_line)
        return -1
    except Exception as e:
        raise RapidFileToolkitVersionNotDetectedError(
            "Failed to detect FlashBlade Toolkit version"
        ) from e
    finally:
        await proc.wait()


async def _run(cmd_name: str, cmdargs: Sequence[bytes]) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmdargs,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode is not None and proc.returncode != 0:
        raise PureStorageCommandFailedError(f'"{cmd_name}" command failed: {err!r}')
    return out.decode()


class RapidFileToolkitClient:
    """Runs the RapidFile Toolkit v1 commands (``pcp``, ``prm``, ``pls``, ``pdu``)."""

    _pls_output_flag: ClassVar[bytes] = b"--json"
    _pdu_usage_flags: ClassVar[tuple[bytes, ...]] = (b"-0", b"-b", b"-a", b"-s")

    async def copy_tree(self, src_path: Path, dst_path: Path) -> None:
        extra_opts: list[bytes] = []
        if src_path.is_dir():
            extra_opts.append(b"-r")
        await _run(
            "pcp",
            [b"pcp", *extra_opts, b"-p", os.fsencode(src_path), os.fsencode(dst_path)],
        )

    async def delete_tree(self, path: Path) -> None:
        await _run("prm", [b"prm", b"-r", os.fsencode(path)])

    def _parse_mode(self, raw_mode: int) -> int:
        """``pls`` v1 prints the octal mode as decimal digits (644 means 0o644)."""
        return int(str(raw_mode), 8)

    async def scan_tree(self, path: Path) -> AsyncIterator[RapidFileEntry]:
        proc = await asyncio.create_subprocess_exec(
            b"pls",
            self._pls_output_flag,
            os.fsencode(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        if proc.stdout is None:
            raise PureStorageStdoutNotAvailableError("pls process stdout is not available")
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                item = load_json(line.rstrip(b"\n"))
                item_path = Path(item["path"])
                entry_type = RapidFileEntryType.FILE
                if item["filetype"] == S_IFDIR:
                    entry_type = RapidFileEntryType.DIRECTORY
                if item["filetype"] == S_IFLNK:
                    entry_type = RapidFileEntryType.SYMLINK
                yield RapidFileEntry(
                    name=item_path.name,
                    path=item_path,
                    type=entry_type,
                    stat=RapidFileStat(
                        size=item["size"],
                        owner=str(item["uid"]),
                        mode=self._parse_mode(item["mode"]),
                        modified=datetime.fromtimestamp(item["mtime"], tz=UTC),
                        created=datetime.fromtimestamp(item["ctime"], tz=UTC),
                    ),
                    symlink_target="",
                )
        finally:
            await proc.wait()

    async def scan_tree_usage(self, path: Path) -> RapidFileTreeUsage:
        total_size = 0
        total_count = 0
        raw_target_path = os.fsencode(path)
        proc = await asyncio.create_subprocess_exec(
            b"pdu",
            *self._pdu_usage_flags,
            raw_target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        if proc.stdout is None:
            raise PureStorageStdoutNotAvailableError("pdu process stdout is not available")
        try:
            line: bytes = b""
            while True:
                try:
                    line = await proc.stdout.readuntil(b"\0")
                except asyncio.IncompleteReadError:
                    break
                size, name = line.rstrip(b"\0").split(maxsplit=1)
                if len(name) != len(raw_target_path) and name != raw_target_path:
                    total_size += int(size)
                    total_count += 1
        finally:
            await proc.wait()
        return RapidFileTreeUsage(file_count=total_count, used_bytes=total_size)

    async def scan_tree_size(self, path: Path) -> BinarySize:
        proc = await asyncio.create_subprocess_exec(
            b"pdu",
            b"-hs",
            os.fsencode(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise PureStorageCommandFailedError(f"pdu command failed: {stderr.decode()}")
        used_bytes, _ = stdout.decode().split()
        return BinarySize.finite_from_str(used_bytes)


class RapidFileToolkitV2Client(RapidFileToolkitClient):
    """Runs the RapidFile Toolkit v2 commands (``pcopy``, ``pls --jsonlines``)."""

    _pls_output_flag: ClassVar[bytes] = b"--jsonlines"
    _pdu_usage_flags: ClassVar[tuple[bytes, ...]] = (b"-0", b"-b", b"-a")

    @override
    async def copy_tree(self, src_path: Path, dst_path: Path) -> None:
        extra_opts: list[bytes] = []
        if src_path.is_dir():
            extra_opts.append(b"-r")
        if dst_path.is_dir():
            extra_opts.append(b"-T")
        await _run(
            "pcopy",
            [b"pcopy", *extra_opts, b"-p", os.fsencode(src_path), os.fsencode(dst_path)],
        )

    @override
    def _parse_mode(self, raw_mode: int) -> int:
        return raw_mode
