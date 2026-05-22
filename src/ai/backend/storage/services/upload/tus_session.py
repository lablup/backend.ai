"""
Metadata-driven TUS upload session.

A single TUS upload session backed by a directory:

    <root>/
      info.json                   # the source of truth (atomic rename writes)
      info.json.<token>.tmp       # transient files used for atomic rename
      .lock                       # fcntl.flock target, scoped to info.json access
      chunks/
        chunk_<offset>.dat        # committed chunks, named by absolute byte offset
        chunk_<offset>.<token>.tmp

The session is safe against multiple Storage Proxy replicas writing to the same
NFS-mounted directory: chunk payloads are written without holding the lock,
and only the short metadata read-modify-write window is serialized via
``fcntl.flock`` on ``.lock``.

PATCH requests with overlapping offsets are de-duplicated by ``(offset, length,
sha256)``; conflicting writes raise ``ChunkConflictError``.
"""

from __future__ import annotations

import asyncio
import dataclasses
import errno
import fcntl
import hashlib
import json
import os
import secrets
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any, Protocol, Self

from ai.backend.storage.errors.upload import (
    ChunkConflictError,
    UploadSessionCorruptedError,
)

INFO_FILENAME = "info.json"
LOCK_FILENAME = ".lock"
CHUNKS_DIRNAME = "chunks"
CHUNK_FILENAME_FMT = "chunk_{offset}.dat"
TEMP_SUFFIX_BYTES = 8


@dataclass(frozen=True, slots=True)
class ChunkRecord:
    offset: int
    length: int
    sha256: str

    @property
    def end(self) -> int:
        return self.offset + self.length

    def to_json(self) -> dict[str, int | str]:
        return {"offset": self.offset, "length": self.length, "sha256": self.sha256}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        return cls(
            offset=int(data["offset"]),
            length=int(data["length"]),
            sha256=str(data["sha256"]),
        )


@dataclass(frozen=True, slots=True)
class SessionState:
    session_id: str
    total_size: int
    received: tuple[ChunkRecord, ...]
    status: str

    @property
    def committed_offset(self) -> int:
        """End offset of the largest contiguous prefix from byte 0."""
        cursor = 0
        for rec in self.received:
            if rec.offset != cursor:
                break
            cursor = rec.end
        return cursor

    @property
    def is_complete(self) -> bool:
        return self.status == "completed" or (
            self.committed_offset >= self.total_size and self.total_size > 0
        )

    def find_at_offset(self, offset: int) -> ChunkRecord | None:
        for rec in self.received:
            if rec.offset == offset:
                return rec
            if rec.offset > offset:
                return None
        return None

    def missing_ranges(self) -> list[tuple[int, int]]:
        """
        Return the list of ``(offset, length)`` byte ranges in
        ``[0, total_size)`` that are NOT yet covered by any received chunk.

        Overlapping or out-of-bounds received chunks are tolerated: ranges are
        coalesced and clipped against the declared total size.
        """
        if self.total_size <= 0:
            return []
        covered: list[tuple[int, int]] = []
        for rec in self.received:
            start = max(0, rec.offset)
            end = min(self.total_size, rec.end)
            if start < end:
                covered.append((start, end))
        if not covered:
            return [(0, self.total_size)]
        covered.sort()
        merged: list[tuple[int, int]] = [covered[0]]
        for start, end in covered[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))
        gaps: list[tuple[int, int]] = []
        cursor = 0
        for start, end in merged:
            if cursor < start:
                gaps.append((cursor, start - cursor))
            cursor = end
        if cursor < self.total_size:
            gaps.append((cursor, self.total_size - cursor))
        return gaps

    def progress_percent(self) -> float:
        if self.total_size <= 0:
            return 100.0
        return round(100.0 * self.committed_offset / self.total_size, 2)

    def to_json(self) -> dict[str, object]:
        return {
            "session": self.session_id,
            "total_size": self.total_size,
            "received": [rec.to_json() for rec in self.received],
            "status": self.status,
            "updated_at": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        raw_received = data.get("received", [])
        if not isinstance(raw_received, list):
            raise UploadSessionCorruptedError("'received' must be a list")
        records: list[ChunkRecord] = []
        for item in raw_received:
            if not isinstance(item, dict):
                raise UploadSessionCorruptedError("malformed chunk record")
            records.append(ChunkRecord.from_json(item))
        records.sort(key=lambda r: r.offset)
        return cls(
            session_id=str(data["session"]),
            total_size=int(data["total_size"]),
            received=tuple(records),
            status=str(data.get("status", "pending")),
        )

    @classmethod
    def empty(cls, session_id: str, total_size: int) -> Self:
        return cls(
            session_id=session_id,
            total_size=total_size,
            received=(),
            status="pending",
        )

    def with_record(self, record: ChunkRecord) -> Self:
        merged = list(self.received)
        merged.append(record)
        merged.sort(key=lambda r: r.offset)
        return dataclasses.replace(self, received=tuple(merged))

    def with_status(self, status: str) -> Self:
        return dataclasses.replace(self, status=status)


@dataclass(frozen=True, slots=True)
class ChunkAcceptance:
    """Result of attempting to commit a chunk."""

    state: SessionState
    committed: bool  # False means duplicate (idempotent) replay
    completed_now: bool  # True if this commit just completed the upload


class TusUploadSession:
    """
    A TUS upload session backed by a chunks-per-offset directory layout.

    Instances are cheap to construct; all state lives on disk under ``root``.
    """

    def __init__(self, root: Path, session_id: str, total_size: int) -> None:
        self._root = root
        self._session_id = session_id
        self._total_size = total_size

    @property
    def root(self) -> Path:
        return self._root

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def chunks_dir(self) -> Path:
        return self._root / CHUNKS_DIRNAME

    @property
    def info_path(self) -> Path:
        return self._root / INFO_FILENAME

    @property
    def lock_path(self) -> Path:
        return self._root / LOCK_FILENAME

    async def ensure_initialized(self) -> SessionState:
        """Create the on-disk layout and an initial info.json if missing."""
        return await asyncio.to_thread(self._ensure_initialized_sync)

    def _ensure_initialized_sync(self) -> SessionState:
        self._root.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        with self._locked():
            existing = self._read_info_locked()
            if existing is not None:
                return existing
            state = SessionState.empty(self._session_id, self._total_size)
            self._write_info_locked(state)
            return state

    async def read_state(self) -> SessionState:
        return await asyncio.to_thread(self._read_state_sync)

    def _read_state_sync(self) -> SessionState:
        # info.json is always rewritten via atomic rename, so a lock-free read
        # observes a fully consistent snapshot (either the old or the new file,
        # never a partial mix). Skip the lock to keep read_state() usable when
        # the session directory does not yet exist.
        if not self.info_path.exists():
            return SessionState.empty(self._session_id, self._total_size)
        state = self._read_info_locked()
        if state is None:
            return SessionState.empty(self._session_id, self._total_size)
        return state

    async def commit_chunk(
        self,
        offset: int,
        chunk_path: Path,
        length: int,
        sha256: str,
    ) -> ChunkAcceptance:
        """
        Promote a fully-written temp chunk file at ``chunk_path`` into the
        session, updating metadata atomically.

        - Same ``(offset, length, sha256)`` already present → idempotent;
          ``chunk_path`` is removed and ``committed=False``.
        - Conflicting record at the same offset → ``ChunkConflictError``;
          ``chunk_path`` is removed.
        - Otherwise the chunk file is renamed into place and the record added.
        """
        return await asyncio.to_thread(self._commit_chunk_sync, offset, chunk_path, length, sha256)

    def _commit_chunk_sync(
        self,
        offset: int,
        chunk_path: Path,
        length: int,
        sha256: str,
    ) -> ChunkAcceptance:
        target = self.chunks_dir / CHUNK_FILENAME_FMT.format(offset=offset)
        with self._locked():
            state = self._read_info_locked()
            if state is None:
                state = SessionState.empty(self._session_id, self._total_size)

            existing = state.find_at_offset(offset)
            if existing is not None:
                _unlink_quietly(chunk_path)
                if existing.length == length and existing.sha256 == sha256:
                    return ChunkAcceptance(state=state, committed=False, completed_now=False)
                raise ChunkConflictError(
                    f"chunk at offset {offset} already exists with different content"
                )

            chunk_path.replace(target)
            new_state = state.with_record(ChunkRecord(offset, length, sha256))
            self._write_info_locked(new_state)
            completed_now = (
                state.committed_offset < new_state.total_size <= new_state.committed_offset
                and new_state.total_size > 0
            )
            return ChunkAcceptance(state=new_state, committed=True, completed_now=completed_now)

    async def assemble(self, target_path: Path) -> None:
        """Concatenate all chunks in offset order into ``target_path``."""
        await asyncio.to_thread(self._assemble_sync, target_path)

    def _assemble_sync(self, target_path: Path) -> None:
        with self._locked():
            state = self._read_info_locked()
            if state is None:
                raise UploadSessionCorruptedError("no session metadata to assemble")
            if state.status == "completed":
                return
            if state.committed_offset < state.total_size:
                raise UploadSessionCorruptedError("cannot assemble: not all chunks received")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            staging = target_path.with_name(f"{target_path.name}.{_random_token()}.tmp")
            try:
                with staging.open("wb") as out:
                    for rec in state.received:
                        chunk_file = self.chunks_dir / CHUNK_FILENAME_FMT.format(offset=rec.offset)
                        with chunk_file.open("rb") as chunk_fp:
                            shutil.copyfileobj(chunk_fp, out, length=1024 * 1024)
                staging.replace(target_path)
            except BaseException:
                _unlink_quietly(staging)
                raise
            self._write_info_locked(state.with_status("completed"))

    async def cleanup(self) -> None:
        """Remove the session directory (chunks + metadata)."""
        await asyncio.to_thread(self._cleanup_sync)

    def _cleanup_sync(self) -> None:
        if not self._root.exists():
            return
        shutil.rmtree(self._root, ignore_errors=True)

    def open_temp_chunk(self, offset: int) -> _TempChunkFile:
        """
        Allocate a unique temp file under chunks/ for a chunk at ``offset``.
        The caller writes payload bytes into ``.path`` and then passes that
        path to :meth:`commit_chunk`.
        """
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        token = _random_token()
        return _TempChunkFile(
            path=self.chunks_dir / f"chunk_{offset}.{token}.tmp",
            offset=offset,
        )

    @contextmanager
    def _locked(self) -> Iterator[IO[bytes]]:
        fd = self.lock_path.open("a+b")
        try:
            fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
            try:
                yield fd
            finally:
                fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
        finally:
            fd.close()

    def _read_info_locked(self) -> SessionState | None:
        if not self.info_path.exists():
            return None
        try:
            raw = self.info_path.read_bytes()
        except FileNotFoundError:
            return None
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise UploadSessionCorruptedError(f"info.json is not valid JSON: {e}") from e
        if not isinstance(data, dict):
            raise UploadSessionCorruptedError("info.json must be a JSON object")
        return SessionState.from_json(data)

    def _write_info_locked(self, state: SessionState) -> None:
        token = _random_token()
        tmp_path = self._root / f"{INFO_FILENAME}.{token}.tmp"
        payload = json.dumps(state.to_json(), separators=(",", ":")).encode("utf-8")
        with tmp_path.open("wb") as fp:
            fp.write(payload)
            fp.flush()
            os.fsync(fp.fileno())
        tmp_path.replace(self.info_path)


@dataclass(slots=True)
class _TempChunkFile:
    path: Path
    offset: int


def _random_token() -> str:
    return secrets.token_hex(TEMP_SUFFIX_BYTES)


def _unlink_quietly(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


class _AsyncByteReader(Protocol):
    async def read(self, n: int) -> bytes: ...


async def stream_chunk_to_temp(
    request_reader: _AsyncByteReader,
    temp_path: Path,
    read_chunk_size: int,
) -> tuple[int, str]:
    """
    Drain ``request_reader`` into ``temp_path`` and return ``(length, sha256)``.

    ``request_reader`` is anything with an async ``read(n)`` method that yields
    ``b""`` at EOF (e.g. ``aiohttp.web.Request.content``).
    """
    hasher = hashlib.sha256()
    total = 0
    loop = asyncio.get_running_loop()
    fp = await loop.run_in_executor(None, lambda: temp_path.open("wb"))
    try:
        while True:
            chunk = await request_reader.read(read_chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
            total += len(chunk)
            await loop.run_in_executor(None, fp.write, chunk)
        await loop.run_in_executor(None, fp.flush)
        await loop.run_in_executor(None, os.fsync, fp.fileno())
    finally:
        await loop.run_in_executor(None, fp.close)
    return total, hasher.hexdigest()
