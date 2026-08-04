from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import stat
import tarfile
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

import zmq

from .logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger())

LIST_FILES: Final = "list-files"
UPLOAD_FILE: Final = "upload-file"
DOWNLOAD_FILE: Final = "download-file"
DOWNLOAD_SINGLE: Final = "download-single"
GET_LOGS: Final = "get-logs"

FILES_RESULT: Final = b"files-result"
TRANSFER_RESULT: Final = b"transfer-result"
LOGS_RESULT: Final = b"logs-result"

GUEST_VERBS: Final = frozenset({
    LIST_FILES,
    UPLOAD_FILE,
    DOWNLOAD_FILE,
    DOWNLOAD_SINGLE,
    GET_LOGS,
})

REPLY_FRAMES: Final[Mapping[str, bytes]] = {
    LIST_FILES: FILES_RESULT,
    UPLOAD_FILE: TRANSFER_RESULT,
    DOWNLOAD_FILE: TRANSFER_RESULT,
    DOWNLOAD_SINGLE: TRANSFER_RESULT,
    GET_LOGS: LOGS_RESULT,
}

HOME_DIR: Final = Path("/home/work")
LOG_DIR: Final = HOME_DIR / ".logs"
MAX_ARCHIVE_BYTES: Final = 1048576
MAX_LOG_BYTES: Final = 1048576

PROFILE_PATH: Final = Path("/run/backend.ai/profile.json")
SUDOERS_DIR: Final = Path("/etc/sudoers.d")
SUDOERS_ENTRY: Final = SUDOERS_DIR / "01-bai-work"
SUDOERS_LINE: Final = "work ALL=(ALL:ALL) NOPASSWD:ALL\n"


class _CappedBuffer(io.BytesIO):
    def write(self, data: Any) -> int:
        if self.tell() + len(data) > MAX_ARCHIVE_BYTES:
            raise ValueError("Too large archive file exceeding 1 MiB")
        return super().write(data)


def _contained(raw: Any) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ValueError("the request carries no path")
    home = HOME_DIR.resolve(strict=False)
    target = Path(os.path.normpath(str(home / raw))).resolve(strict=False)
    if target != home and not target.is_relative_to(home):
        raise PermissionError(f"{raw} resolves outside /home/work")
    return target


def _scan(target: Path) -> tuple[list[dict[str, Any]], str]:
    files: list[dict[str, Any]] = []
    errors: list[str] = []
    for entry in os.scandir(target):
        try:
            fstat = entry.stat(follow_symlinks=False)
        except OSError as e:
            errors.append(f"{entry.name}: {e}")
            continue
        files.append({
            "mode": stat.filemode(fstat.st_mode),
            "size": fstat.st_size,
            "ctime": fstat.st_ctime,
            "mtime": fstat.st_mtime,
            "atime": fstat.st_atime,
            "filename": entry.name,
        })
    return files, "\n".join(errors)


def _store(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def _archive(target: Path) -> bytes:
    if not target.exists():
        raise FileNotFoundError(f"{target} does not exist inside the guest")
    buffer = _CappedBuffer()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        tar.add(str(target), arcname=target.name, recursive=True)
    archived = buffer.getvalue()
    if not archived:
        raise ValueError(f"the archive of {target} came out empty")
    return archived


def _extract_single(target: Path) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(_archive(target))) as tar:
        names = tar.getnames()
        if len(names) != 1:
            raise ValueError(f"Expected a single-file archive but found {len(names)} from {target}")
        member = tar.extractfile(names[0])
        if member is None:
            raise ValueError(f"Could not read {names[0]!r} out of the archive of {target}")
        content = member.read()
    if not content:
        raise ValueError(f"{target} carries no content to download")
    return content


def _log_path() -> Path | None:
    kernel_id = os.environ.get("BACKENDAI_KERNEL_ID")
    if not kernel_id or not LOG_DIR.is_dir():
        return None
    try:
        hexed = uuid.UUID(kernel_id).hex
    except ValueError:
        return None
    return LOG_DIR / "task" / hexed[:2] / hexed[2:4] / f"{hexed[4:]}.log"


def _read_log() -> tuple[bytes, bool]:
    path = _log_path()
    if path is None or not path.is_file():
        return b"", False
    size = path.stat().st_size
    with path.open("rb") as fp:
        if size > MAX_LOG_BYTES:
            fp.seek(size - MAX_LOG_BYTES)
            return fp.read(), True
        return fp.read(), False


async def _dispatch(
    verb: str, header: Mapping[str, Any], body: bytes
) -> tuple[dict[str, Any], bytes]:
    if verb == LIST_FILES:
        target = await asyncio.to_thread(_contained, header.get("path"))
        files, errors = await asyncio.to_thread(_scan, target)
        return {"files": files, "errors": errors, "abspath": str(header.get("path"))}, b""
    if verb == UPLOAD_FILE:
        target = await asyncio.to_thread(_contained, header.get("path"))
        await asyncio.to_thread(_store, target, body)
        return {}, b""
    if verb == DOWNLOAD_FILE:
        target = await asyncio.to_thread(_contained, header.get("path"))
        return {}, await asyncio.to_thread(_archive, target)
    if verb == DOWNLOAD_SINGLE:
        target = await asyncio.to_thread(_contained, header.get("path"))
        return {}, await asyncio.to_thread(_extract_single, target)
    if verb == GET_LOGS:
        logs, truncated = await asyncio.to_thread(_read_log)
        return {"truncated": truncated}, logs
    raise ValueError(f"{verb} is not an in-guest file operation")


async def _send(
    outsock: zmq.Socket[Any], frame: bytes, header: Mapping[str, Any], body: bytes
) -> None:
    await outsock.send_multipart([frame, json.dumps(header).encode("utf-8") + b"\n" + body])


async def serve(outsock: zmq.Socket[Any], verb: str, payload: bytes) -> None:
    frame = REPLY_FRAMES.get(verb, TRANSFER_RESULT)
    line, _, body = payload.partition(b"\n")
    request_id = ""
    try:
        header = json.loads(line)
        request_id = str(header.get("req", ""))
        reply, answer = await _dispatch(verb, header, body)
    except Exception as e:
        try:
            await _send(
                outsock,
                frame,
                {"req": request_id, "ok": False, "error": f"{type(e).__name__}: {e}"},
                b"",
            )
        except Exception:
            log.exception("guestops: could not report the {} failure", verb)
        return
    await _send(outsock, frame, {**reply, "req": request_id, "ok": True}, answer)


def _write_sudoers() -> None:
    SUDOERS_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)
    SUDOERS_ENTRY.write_text(SUDOERS_LINE)
    SUDOERS_ENTRY.chmod(0o440)


async def apply_guest_sudo() -> None:
    if not await asyncio.to_thread(PROFILE_PATH.is_file):
        return
    try:
        profile = json.loads(await asyncio.to_thread(PROFILE_PATH.read_text))
    except (OSError, ValueError):
        log.warning("guestops: the guest profile is unreadable; leaving sudo untouched")
        return
    if not profile.get("allow_sudo"):
        return
    try:
        await asyncio.to_thread(_write_sudoers)
    except OSError as e:
        log.warning("guestops: could not grant sudo inside the guest ({})", e)
