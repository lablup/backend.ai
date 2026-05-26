"""Valkey-backed TUS upload session.

Session metadata lives in Valkey (via :class:`ValkeyTusClient`), guarded by a
per-session distributed lock from an injected :class:`DistributedLockFactory`.
Chunk payload bytes live on the shared filesystem, content-addressed by
``(offset, sha256)``::

    <session_dir>/
      chunks/
        chunk_<offset>.dat
        chunk_<offset>.<token>.tmp
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from pathlib import Path

import aiofiles
import aiofiles.os

from ai.backend.common.clients.valkey_client.valkey_tus import ValkeyTusClient
from ai.backend.common.lock import AbstractDistributedLock, DistributedLockFactory
from ai.backend.common.types import StreamReader, TusSessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.storage.errors.upload import (
    ChunkConflictError,
    UploadSessionCorruptedError,
)

from .lock import LOCK_KEY_PREFIX, LOCK_LIFETIME_SECONDS
from .types import (
    ChunkCommitResult,
    ChunkMetadata,
    TusSessionState,
    TusUploadSessionArgs,
    UploadStatus,
    WrittenChunk,
)
from .utils import (
    CHUNKS_DIRNAME,
    committed_chunk_path,
    staging_path,
    temp_chunk_path,
    unlink_quietly,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class TusUploadSession:
    """
    A TUS upload session whose metadata lives in Valkey and whose chunk payloads
    live under ``session_dir`` on the shared filesystem.

    Instances are cheap to construct; all state lives in Valkey (metadata) and on
    disk (chunk bytes). The metadata read-modify-write window is serialized across
    replicas by a per-session distributed lock obtained from the injected
    :class:`DistributedLockFactory`.
    """

    _session_dir: Path
    _session_id: TusSessionId
    _total_size: int
    _valkey: ValkeyTusClient
    _lock_factory: DistributedLockFactory

    def __init__(self, args: TusUploadSessionArgs) -> None:
        self._session_dir = args.session_dir
        self._session_id = args.session_id
        self._total_size = args.total_size
        self._valkey = args.valkey_client
        self._lock_factory = args.lock_factory

    @property
    def session_dir(self) -> Path:
        return self._session_dir

    @property
    def session_id(self) -> TusSessionId:
        return self._session_id

    @property
    def chunks_dir(self) -> Path:
        return self._session_dir / CHUNKS_DIRNAME

    @property
    def _lock_key(self) -> str:
        return f"{LOCK_KEY_PREFIX}:{self._session_id}"

    def _lock(self) -> AbstractDistributedLock:
        return self._lock_factory(self._lock_key, LOCK_LIFETIME_SECONDS)

    async def _load_state(self) -> TusSessionState | None:
        raw = await self._valkey.get_session_state(self._session_id)
        if raw is None:
            return None
        return TusSessionState.model_validate_json(raw)

    async def _store_state(self, state: TusSessionState) -> None:
        await self._valkey.set_session_state(self._session_id, state.model_dump_json())

    async def ensure_initialized(self) -> None:
        """Create an initial Valkey state for this session if missing.

        If the state is absent but ``chunks_dir`` still holds files, those are
        leftovers from a prior session whose Valkey state expired by TTL. The
        new state would not know about them and could silently mix their bytes
        into the assembled output, so drop them before starting fresh.
        """
        async with self._lock():
            if await self._load_state() is not None:
                return
            await self._delete_chunk_files()
            await self._store_state(TusSessionState.empty(self._session_id, self._total_size))

    async def exists(self) -> bool:
        """Return True iff a Valkey state currently exists for this session.

        Valkey is the source of truth — a missing state means the session was
        never registered or its TTL elapsed, regardless of what is on disk.
        """
        return (await self._load_state()) is not None

    async def read_state(self) -> TusSessionState:
        state = await self._load_state()
        if state is None:
            return TusSessionState.empty(self._session_id, self._total_size)
        return state

    def open_temp_chunk(self, offset: int) -> Path:
        """
        Allocate a unique temp file path under chunks/ for a chunk at
        ``offset``. The caller writes payload bytes into the returned path and
        then passes it to :meth:`commit_chunk`.
        """
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        return temp_chunk_path(self.chunks_dir, offset)

    async def write_temp_chunk(self, offset: int, reader: StreamReader) -> WrittenChunk:
        """
        Open a fresh temp chunk file for ``offset``, drain ``reader`` into it,
        and return the resulting :class:`WrittenChunk`.

        ``reader`` is the common :class:`StreamReader`; its ``read()`` yields
        the body in bounded chunks (granularity owned by the concrete reader,
        e.g. the PATCH-body adapter built in the handler), so only one chunk is
        held in memory at a time. The temp file is removed if draining fails;
        otherwise the caller promotes it via :meth:`commit_chunk`.
        """
        temp_path = self.open_temp_chunk(offset)
        hasher = hashlib.sha256()
        total = 0
        try:
            async with aiofiles.open(temp_path, "wb") as chunk_file:
                async for chunk in reader.read():
                    hasher.update(chunk)
                    total += len(chunk)
                    await chunk_file.write(chunk)
                await chunk_file.flush()
                await asyncio.to_thread(os.fsync, chunk_file.fileno())
        except BaseException:
            await unlink_quietly(temp_path)
            raise
        return WrittenChunk(path=temp_path, length=total, sha256=hasher.hexdigest())

    async def commit_chunk(
        self,
        offset: int,
        chunk_path: Path,
        length: int,
        sha256: str,
    ) -> ChunkCommitResult:
        """
        Promote a fully-written temp chunk file at ``chunk_path`` into the
        session, updating Valkey metadata under the per-session lock.

        - Same ``(offset, length, sha256)`` already present → idempotent;
          ``chunk_path`` is removed and ``committed=False``.
        - Conflicting record at the same offset → ``ChunkConflictError``;
          ``chunk_path`` is removed.
        - Already-completed session → idempotent no-op (a late duplicate that
          raced completion on another replica); ``chunk_path`` is removed.
        - Otherwise the chunk file is renamed into place and the record added.
        """
        target = committed_chunk_path(self.chunks_dir, offset)
        async with self._lock():
            state = await self._load_state()
            if state is None:
                # `ensure_initialized` must run before `commit_chunk`; reaching
                # here means either the caller skipped it or the Valkey state
                # disappeared (TTL/external delete). Either way, the session is
                # not in a coherent state to accept new chunks. Drop the temp
                # chunk file so it does not leak under the chunks dir.
                await unlink_quietly(chunk_path)
                raise UploadSessionCorruptedError(
                    f"upload session {self._session_id} has no metadata at commit time"
                )

            # Late duplicate PATCH: another replica already assembled and marked
            # COMPLETED. Drop the temp file silently and return a no-op so the
            # client observes idempotent success rather than an error.
            if state.status == UploadStatus.COMPLETED:
                await unlink_quietly(chunk_path)
                return ChunkCommitResult(state=state, committed=False, is_final_commit=False)

            existing = state.find_at_offset(offset)
            if existing is not None:
                await unlink_quietly(chunk_path)
                if existing.length == length and existing.sha256 == sha256:
                    return ChunkCommitResult(state=state, committed=False, is_final_commit=False)
                raise ChunkConflictError(
                    f"chunk at offset {offset} already exists with different content"
                )

            await aiofiles.os.replace(chunk_path, target)
            previous_committed_offset = state.committed_offset
            state.append_chunk(ChunkMetadata(offset=offset, length=length, sha256=sha256))
            await self._store_state(state)
            is_final_commit = (
                previous_committed_offset < state.total_size <= state.committed_offset
                and state.total_size > 0
            )
            progress_percent = (
                100.0 * state.committed_offset / state.total_size if state.total_size > 0 else 0.0
            )
            log.trace(
                "TUS chunk committed: session={}, offset={}, length={}, progress={}/{} ({:.1f}%)",
                self._session_id,
                offset,
                length,
                state.committed_offset,
                state.total_size,
                progress_percent,
            )
            return ChunkCommitResult(state=state, committed=True, is_final_commit=is_final_commit)

    async def assemble(self, target_path: Path) -> None:
        """Concatenate all chunks in offset order into ``target_path``."""
        async with self._lock():
            state = await self._load_state()
            if state is None:
                raise UploadSessionCorruptedError("no session metadata to assemble")
            if state.status == UploadStatus.COMPLETED:
                return
            if state.committed_offset < state.total_size:
                raise UploadSessionCorruptedError("cannot assemble: not all chunks received")
            await self._assemble_chunks_to_disk(state, target_path)
            state.set_complete()
            await self._store_state(state)
            log.info(
                "TUS upload completed: session={}, target={}, size={} bytes, chunks={}",
                self._session_id,
                target_path,
                state.total_size,
                len(state.committed_chunks),
            )

    async def _assemble_chunks_to_disk(self, state: TusSessionState, target_path: Path) -> None:
        await aiofiles.os.makedirs(target_path.parent, exist_ok=True)
        staging = staging_path(target_path)
        copy_buffer = 1024 * 1024
        try:
            async with aiofiles.open(staging, "wb") as out:
                for rec in state.committed_chunks:
                    chunk_file = committed_chunk_path(self.chunks_dir, rec.offset)
                    async with aiofiles.open(chunk_file, "rb") as chunk_fp:
                        while True:
                            buf = await chunk_fp.read(copy_buffer)
                            if not buf:
                                break
                            await out.write(buf)
            await aiofiles.os.replace(staging, target_path)
        except BaseException:
            await unlink_quietly(staging)
            raise

    async def cleanup(self) -> None:
        """
        Delete chunk payload files after a completed upload.

        Only the chunk files are removed; the Valkey state (status="completed")
        is intentionally kept so a late duplicate PATCH that raced completion on
        another replica observes the completed marker and no-ops instead of
        re-creating a stray session. The marker itself is reclaimed by its
        Valkey TTL.
        """
        async with self._lock():
            state = await self._load_state()
            if state is None or state.status != UploadStatus.COMPLETED:
                return
            await self._delete_chunk_files()

    async def _delete_chunk_files(self) -> None:
        if not await aiofiles.os.path.exists(self.chunks_dir):
            return
        for name in await aiofiles.os.listdir(self.chunks_dir):
            await unlink_quietly(self.chunks_dir / name)
