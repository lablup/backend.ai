"""
Integration tests for the ``TusUploadSession`` storage class.

Metadata + the per-session lock live in a real Valkey (the ``valkey_tus_client``
fixture, backed by a redis container); chunk payloads live under ``tmp_path``.
Nothing is mocked. Concurrency tests fire ``commit_chunk`` coroutines together to
model multiple Storage Proxy replicas hitting the same session.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import json
import secrets
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from ai.backend.common.clients.valkey_client.valkey_tus import ValkeyTusClient
from ai.backend.common.lock import DistributedLockFactory
from ai.backend.common.types import StreamReader, TusSessionId
from ai.backend.storage.errors.upload import (
    ChunkConflictError,
    UploadSessionCorruptedError,
)
from ai.backend.storage.services.upload.tus_session import TusUploadSession
from ai.backend.storage.services.upload.types import (
    ChunkCommitResult,
    ChunkMetadata,
    TusUploadSessionArgs,
    UploadStatus,
)


@dataclasses.dataclass(frozen=True, slots=True)
class _Chunk:
    offset: int
    payload: bytes

    @property
    def length(self) -> int:
        return len(self.payload)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()


class _Reader(StreamReader):
    def __init__(self, data: bytes, chunk_size: int) -> None:
        self._data = data
        self._chunk_size = chunk_size

    async def read(self) -> AsyncIterator[bytes]:
        for start in range(0, len(self._data), self._chunk_size):
            yield self._data[start : start + self._chunk_size]

    def content_type(self) -> str | None:
        return None


def _make_chunks(total_size: int, chunk_size: int, *, seed: bytes = b"abc") -> list[_Chunk]:
    payload = (seed * ((total_size // len(seed)) + 1))[:total_size]
    chunks: list[_Chunk] = []
    for offset in range(0, total_size, chunk_size):
        end = min(offset + chunk_size, total_size)
        chunks.append(_Chunk(offset=offset, payload=payload[offset:end]))
    return chunks


def _write_temp_chunk(session: TusUploadSession, chunk: _Chunk) -> Path:
    temp = session.open_temp_chunk(chunk.offset)
    temp.write_bytes(chunk.payload)
    return temp


async def _commit(session: TusUploadSession, chunk: _Chunk) -> ChunkCommitResult:
    return await session.commit_chunk(
        offset=chunk.offset,
        chunk_path=_write_temp_chunk(session, chunk),
        length=chunk.length,
        sha256=chunk.sha256,
    )


@pytest.fixture
def session_root(tmp_path: Path) -> Path:
    return tmp_path / "session"


@pytest.fixture
def session(
    session_root: Path,
    valkey_tus_client: ValkeyTusClient,
    tus_lock_factory: DistributedLockFactory,
) -> TusUploadSession:
    # A unique session id keeps each test isolated within the shared Valkey.
    return TusUploadSession(
        TusUploadSessionArgs(
            session_dir=session_root,
            session_id=TusSessionId(secrets.token_hex(8)),
            total_size=1024,
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
    )


class TestSessionLifecycle:
    async def test_ensure_initialized_creates_state(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        state = await session.read_state()
        assert state.committed_offset == 0
        assert state.status == UploadStatus.IN_PROGRESS

    async def test_ensure_initialized_is_idempotent(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=512, chunk_size=512)
        await _commit(session, chunks[0])

        # Re-initializing must not wipe the existing state.
        await session.ensure_initialized()
        state = await session.read_state()
        assert state.committed_offset == chunks[0].length

    async def test_read_state_on_missing_info_returns_empty(
        self, session: TusUploadSession
    ) -> None:
        state = await session.read_state()
        assert state.committed_offset == 0
        assert state.committed_chunks == []

    async def test_ensure_initialized_drops_stale_chunks_after_ttl_expiry(
        self, session: TusUploadSession, valkey_tus_client: ValkeyTusClient
    ) -> None:
        # Simulate a session that wrote chunks, then had its Valkey state
        # reclaimed by TTL while leftover chunk files stayed on disk.
        await session.ensure_initialized()
        await _commit(session, _Chunk(offset=0, payload=b"old" * 100))
        await valkey_tus_client.delete_session_state(session.session_id)
        assert list(session.chunks_dir.iterdir())

        # The next ensure_initialized must clear the stale chunks so the fresh
        # state does not silently mix the old bytes into the new upload.
        await session.ensure_initialized()
        assert list(session.chunks_dir.iterdir()) == []
        state = await session.read_state()
        assert state.committed_chunks == []


class TestSequentialCommit:
    async def test_commits_advance_committed_offset(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=256)
        last_commit_result: ChunkCommitResult | None = None
        for chunk in chunks:
            last_commit_result = await _commit(session, chunk)
        assert last_commit_result is not None
        assert last_commit_result.state.committed_offset == 1024
        assert last_commit_result.is_final_commit is True

    async def test_is_final_commit_fires_only_on_threshold_crossing(
        self, session: TusUploadSession
    ) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=512)
        first = await _commit(session, chunks[0])
        last = await _commit(session, chunks[1])
        assert first.is_final_commit is False
        assert last.is_final_commit is True


class TestOutOfOrderCommit:
    async def test_prefix_only_advances_when_gap_filled(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=256)
        result = await _commit(session, chunks[3])
        assert result.state.committed_offset == 0
        await _commit(session, chunks[2])
        await _commit(session, chunks[1])
        final = await _commit(session, chunks[0])
        assert final.state.committed_offset == 1024
        assert final.is_final_commit is True


class TestIdempotencyAndConflict:
    async def test_duplicate_chunk_is_idempotent(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=512, chunk_size=512)
        first = await _commit(session, chunks[0])
        assert first.committed is True
        replay = await _commit(session, chunks[0])
        assert replay.committed is False
        assert replay.state.committed_offset == 512

    async def test_conflicting_chunk_raises(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        original = _Chunk(offset=0, payload=b"A" * 512)
        await _commit(session, original)

        tampered = _Chunk(offset=0, payload=b"B" * 512)
        with pytest.raises(ChunkConflictError):
            await _commit(session, tampered)

        state = await session.read_state()
        assert state.committed_chunks == [
            ChunkMetadata(offset=0, length=512, sha256=original.sha256)
        ]

    async def test_conflicting_chunk_temp_file_is_cleaned_up(
        self, session: TusUploadSession
    ) -> None:
        await session.ensure_initialized()
        await _commit(session, _Chunk(offset=0, payload=b"A" * 512))

        temp = session.open_temp_chunk(0)
        temp.write_bytes(b"B" * 512)
        with pytest.raises(ChunkConflictError):
            await session.commit_chunk(
                offset=0,
                chunk_path=temp,
                length=512,
                sha256=hashlib.sha256(b"B" * 512).hexdigest(),
            )
        assert not temp.exists()


class TestAssembly:
    async def test_assembled_file_matches_payload(
        self, session: TusUploadSession, tmp_path: Path
    ) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=128)
        for chunk in chunks:
            await _commit(session, chunk)

        target = tmp_path / "out" / "final.bin"
        await session.assemble(target)

        expected = b"".join(c.payload for c in chunks)
        assert target.read_bytes() == expected

    async def test_assemble_is_idempotent_on_completed_status(
        self, session: TusUploadSession, tmp_path: Path
    ) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=1024)
        await _commit(session, chunks[0])

        target = tmp_path / "out" / "final.bin"
        await session.assemble(target)
        first_mtime = target.stat().st_mtime_ns

        await session.assemble(target)
        assert target.stat().st_mtime_ns == first_mtime

    async def test_assemble_before_completion_raises(
        self, session: TusUploadSession, tmp_path: Path
    ) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=512)
        await _commit(session, chunks[0])

        with pytest.raises(UploadSessionCorruptedError):
            await session.assemble(tmp_path / "final.bin")

    async def test_cleanup_reclaims_chunks_but_keeps_completed_marker(
        self, session: TusUploadSession, tmp_path: Path
    ) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=1024)
        await _commit(session, chunks[0])
        await session.assemble(tmp_path / "final.bin")
        await session.cleanup()

        # Chunk data is reclaimed...
        assert list(session.chunks_dir.glob("*.dat")) == []
        # ...but the completed marker is intentionally kept in Valkey (reclaimed
        # by its TTL) so that late duplicate PATCHes can no-op instead of racing
        # a teardown.
        assert (await session.read_state()).status == UploadStatus.COMPLETED

    async def test_late_commit_after_completion_is_idempotent_noop(
        self, session: TusUploadSession, tmp_path: Path
    ) -> None:
        """A duplicate chunk that arrives after the upload completed (and was
        cleaned up) must no-op, not crash — this is the multi-proxy race the
        real-NFS reproduction surfaced."""
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=1024)
        await _commit(session, chunks[0])
        await session.assemble(tmp_path / "final.bin")
        await session.cleanup()

        # A late retry of the same chunk lands now.
        result = await _commit(session, chunks[0])
        assert result.committed is False
        assert result.is_final_commit is False
        assert result.state.status == UploadStatus.COMPLETED


class TestCorruption:
    async def test_garbage_state_raises(
        self, session: TusUploadSession, valkey_tus_client: ValkeyTusClient
    ) -> None:
        await valkey_tus_client.set_session_state(session.session_id, "{not json")
        with pytest.raises(UploadSessionCorruptedError):
            await session.read_state()

    async def test_non_object_state_raises(
        self, session: TusUploadSession, valkey_tus_client: ValkeyTusClient
    ) -> None:
        await valkey_tus_client.set_session_state(session.session_id, json.dumps([1, 2, 3]))
        with pytest.raises(UploadSessionCorruptedError):
            await session.read_state()


class TestConcurrentCommits:
    """Models multiple Storage Proxy replicas hitting the same session."""

    async def test_concurrent_disjoint_offsets_all_succeed(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=4096, chunk_size=256)

        results = await asyncio.gather(*(_commit(session, chunk) for chunk in chunks))

        assert all(r.committed for r in results)
        assert sum(1 for r in results if r.is_final_commit) == 1

        state = await session.read_state()
        assert state.committed_offset == 4096

    async def test_concurrent_same_offset_one_winner(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunk = _Chunk(offset=0, payload=b"x" * 1024)

        results = list(
            await asyncio.gather(
                *(_commit(session, chunk) for _ in range(8)), return_exceptions=True
            )
        )

        winners = [r for r in results if isinstance(r, ChunkCommitResult) and r.committed]
        replays = [r for r in results if isinstance(r, ChunkCommitResult) and not r.committed]
        assert len(winners) == 1
        assert len(winners) + len(replays) == 8


class TestWriteTempChunk:
    async def test_drains_reader_and_hashes_payload(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        payload = b"hello-world" * 500
        reader = _Reader(payload, chunk_size=64)
        written = await session.write_temp_chunk(0, reader)

        assert written.length == len(payload)
        assert written.sha256 == hashlib.sha256(payload).hexdigest()
        assert written.path.read_bytes() == payload
