"""
Tests for the metadata-driven TUS upload session.

These tests exercise the on-disk layout (info.json + chunks/*.dat + .lock)
directly via ``tmp_path``: nothing is mocked. Concurrency tests run the
synchronous internals under ``concurrent.futures`` to model multiple Storage
Proxy replicas hitting the same NFS-mounted session directory.
"""

from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import json
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from ai.backend.storage.errors.upload import (
    ChunkConflictError,
    UploadSessionCorruptedError,
)
from ai.backend.storage.services.upload.tus_session import (
    INFO_FILENAME,
    ChunkAcceptance,
    ChunkRecord,
    SessionState,
    TusUploadSession,
    stream_chunk_to_temp,
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


def _make_chunks(total_size: int, chunk_size: int, *, seed: bytes = b"abc") -> list[_Chunk]:
    payload = (seed * ((total_size // len(seed)) + 1))[:total_size]
    chunks: list[_Chunk] = []
    for offset in range(0, total_size, chunk_size):
        end = min(offset + chunk_size, total_size)
        chunks.append(_Chunk(offset=offset, payload=payload[offset:end]))
    return chunks


def _write_temp_chunk(session: TusUploadSession, chunk: _Chunk) -> Path:
    temp = session.open_temp_chunk(chunk.offset)
    temp.path.write_bytes(chunk.payload)
    return temp.path


async def _commit(session: TusUploadSession, chunk: _Chunk) -> ChunkAcceptance:
    return await session.commit_chunk(
        offset=chunk.offset,
        chunk_path=_write_temp_chunk(session, chunk),
        length=chunk.length,
        sha256=chunk.sha256,
    )


@pytest.fixture
def session_root(tmp_path: Path) -> Path:
    return tmp_path / "session-abc"


@pytest.fixture
def session(session_root: Path) -> TusUploadSession:
    return TusUploadSession(session_root, session_id="abc", total_size=1024)


class TestSessionStatePrefix:
    @pytest.mark.parametrize(
        ("records", "expected_prefix"),
        [
            ([], 0),
            ([ChunkRecord(0, 100, "x")], 100),
            ([ChunkRecord(0, 100, "x"), ChunkRecord(100, 50, "y")], 150),
            # Gap after a contiguous prefix: prefix ends at the gap.
            ([ChunkRecord(0, 100, "x"), ChunkRecord(200, 50, "y")], 100),
            # No prefix from byte 0.
            ([ChunkRecord(50, 100, "x")], 0),
        ],
    )
    def test_committed_offset(self, records: list[ChunkRecord], expected_prefix: int) -> None:
        state = SessionState(
            session_id="s", total_size=1024, received=tuple(records), status="pending"
        )
        assert state.committed_offset == expected_prefix


class TestMissingRanges:
    @pytest.mark.parametrize(
        ("total_size", "records", "expected"),
        [
            # Empty session: the whole declared size is missing.
            (1000, [], [(0, 1000)]),
            # Single chunk at start.
            (1000, [ChunkRecord(0, 400, "x")], [(400, 600)]),
            # Single chunk in the middle.
            (1000, [ChunkRecord(200, 300, "x")], [(0, 200), (500, 500)]),
            # Contiguous prefix.
            (1000, [ChunkRecord(0, 400, "x"), ChunkRecord(400, 100, "y")], [(500, 500)]),
            # Two disjoint chunks leaving two gaps.
            (
                1000,
                [ChunkRecord(0, 200, "x"), ChunkRecord(500, 300, "y")],
                [(200, 300), (800, 200)],
            ),
            # Fully complete: no gaps.
            (500, [ChunkRecord(0, 500, "x")], []),
            # Overlapping/duplicate ranges are coalesced.
            (
                1000,
                [ChunkRecord(0, 600, "x"), ChunkRecord(400, 200, "y")],
                [(600, 400)],
            ),
            # Record extending past total_size is clipped.
            (1000, [ChunkRecord(800, 500, "x")], [(0, 800)]),
        ],
    )
    def test_missing_ranges(
        self,
        total_size: int,
        records: list[ChunkRecord],
        expected: list[tuple[int, int]],
    ) -> None:
        state = SessionState(
            session_id="s",
            total_size=total_size,
            received=tuple(records),
            status="pending",
        )
        assert state.missing_ranges() == expected

    @pytest.mark.parametrize(
        ("total_size", "records", "expected_percent"),
        [
            (1000, [], 0.0),
            (1000, [ChunkRecord(0, 250, "x")], 25.0),
            (1000, [ChunkRecord(0, 500, "x"), ChunkRecord(500, 500, "y")], 100.0),
            # Non-contiguous prefix only counts the contiguous head.
            (1000, [ChunkRecord(500, 500, "x")], 0.0),
            # Zero-size sessions are reported as 100%.
            (0, [], 100.0),
        ],
    )
    def test_progress_percent(
        self,
        total_size: int,
        records: list[ChunkRecord],
        expected_percent: float,
    ) -> None:
        state = SessionState(
            session_id="s",
            total_size=total_size,
            received=tuple(records),
            status="pending",
        )
        assert state.progress_percent() == expected_percent


class TestSessionLifecycle:
    async def test_ensure_initialized_creates_layout(self, session: TusUploadSession) -> None:
        state = await session.ensure_initialized()
        assert state.committed_offset == 0
        assert state.status == "pending"
        assert session.info_path.exists()
        assert session.chunks_dir.is_dir()
        assert session.lock_path.exists()

    async def test_ensure_initialized_is_idempotent(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=512, chunk_size=512)
        await _commit(session, chunks[0])

        # Re-initializing must not wipe the existing state.
        state = await session.ensure_initialized()
        assert state.committed_offset == chunks[0].length

    async def test_read_state_on_missing_info_returns_empty(
        self, session: TusUploadSession
    ) -> None:
        state = await session.read_state()
        assert state.committed_offset == 0
        assert state.received == ()


class TestSequentialCommit:
    async def test_commits_advance_committed_offset(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=256)
        last_acceptance: ChunkAcceptance | None = None
        for chunk in chunks:
            last_acceptance = await _commit(session, chunk)
        assert last_acceptance is not None
        assert last_acceptance.state.committed_offset == 1024
        assert last_acceptance.completed_now is True

    async def test_completed_now_fires_only_on_threshold_crossing(
        self, session: TusUploadSession
    ) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=512)
        first = await _commit(session, chunks[0])
        last = await _commit(session, chunks[1])
        assert first.completed_now is False
        assert last.completed_now is True


class TestOutOfOrderCommit:
    async def test_prefix_only_advances_when_gap_filled(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=256)
        # Commit last chunk first.
        acceptance = await _commit(session, chunks[3])
        assert acceptance.state.committed_offset == 0
        # Fill earlier chunks in reverse order.
        await _commit(session, chunks[2])
        await _commit(session, chunks[1])
        final = await _commit(session, chunks[0])
        assert final.state.committed_offset == 1024
        assert final.completed_now is True


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

        # State must reflect the original chunk only.
        state = await session.read_state()
        assert state.received == (ChunkRecord(0, 512, original.sha256),)

    async def test_conflicting_chunk_temp_file_is_cleaned_up(
        self, session: TusUploadSession
    ) -> None:
        await session.ensure_initialized()
        await _commit(session, _Chunk(offset=0, payload=b"A" * 512))

        temp = session.open_temp_chunk(0)
        temp.path.write_bytes(b"B" * 512)
        with pytest.raises(ChunkConflictError):
            await session.commit_chunk(
                offset=0,
                chunk_path=temp.path,
                length=512,
                sha256=hashlib.sha256(b"B" * 512).hexdigest(),
            )
        assert not temp.path.exists()


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

        # Calling again must not raise nor rewrite the target.
        await session.assemble(target)
        assert target.stat().st_mtime_ns == first_mtime

    async def test_assemble_before_completion_raises(
        self, session: TusUploadSession, tmp_path: Path
    ) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=512)
        await _commit(session, chunks[0])  # only half

        with pytest.raises(UploadSessionCorruptedError):
            await session.assemble(tmp_path / "final.bin")

    async def test_cleanup_removes_session_dir(
        self, session: TusUploadSession, tmp_path: Path
    ) -> None:
        await session.ensure_initialized()
        chunks = _make_chunks(total_size=1024, chunk_size=1024)
        await _commit(session, chunks[0])
        await session.assemble(tmp_path / "final.bin")
        await session.cleanup()
        assert not session.root.exists()


class TestCorruption:
    async def test_garbage_info_json_raises(self, session: TusUploadSession) -> None:
        session.root.mkdir(parents=True, exist_ok=True)
        (session.root / INFO_FILENAME).write_text("{not json")
        with pytest.raises(UploadSessionCorruptedError):
            await session.read_state()

    async def test_non_object_info_json_raises(self, session: TusUploadSession) -> None:
        session.root.mkdir(parents=True, exist_ok=True)
        (session.root / INFO_FILENAME).write_text(json.dumps([1, 2, 3]))
        with pytest.raises(UploadSessionCorruptedError):
            await session.read_state()


class TestConcurrentCommits:
    """Models multiple Storage Proxy replicas hitting the same session."""

    @pytest.fixture
    def disjoint_chunks(self) -> Iterator[list[_Chunk]]:
        yield _make_chunks(total_size=4096, chunk_size=256)

    async def test_concurrent_disjoint_offsets_all_succeed(
        self, session: TusUploadSession, disjoint_chunks: list[_Chunk]
    ) -> None:
        await session.ensure_initialized()

        def worker(chunk: _Chunk) -> ChunkAcceptance:
            return session._commit_chunk_sync(
                offset=chunk.offset,
                chunk_path=_write_temp_chunk(session, chunk),
                length=chunk.length,
                sha256=chunk.sha256,
            )

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [loop.run_in_executor(pool, worker, chunk) for chunk in disjoint_chunks]
            results = await asyncio.gather(*futures)

        assert all(r.committed for r in results)
        assert sum(1 for r in results if r.completed_now) == 1

        state = await session.read_state()
        assert state.committed_offset == 4096

    async def test_concurrent_same_offset_one_winner(self, session: TusUploadSession) -> None:
        await session.ensure_initialized()
        chunk = _Chunk(offset=0, payload=b"x" * 1024)

        def worker() -> ChunkAcceptance:
            return session._commit_chunk_sync(
                offset=chunk.offset,
                chunk_path=_write_temp_chunk(session, chunk),
                length=chunk.length,
                sha256=chunk.sha256,
            )

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [loop.run_in_executor(pool, worker) for _ in range(8)]
            results = list(await asyncio.gather(*futures, return_exceptions=True))

        winners = [r for r in results if isinstance(r, ChunkAcceptance) and r.committed]
        replays = [r for r in results if isinstance(r, ChunkAcceptance) and not r.committed]
        assert len(winners) == 1
        assert len(winners) + len(replays) == 8


class TestStreamChunkToTemp:
    async def test_streams_and_hashes_payload(self, tmp_path: Path) -> None:
        class _Reader:
            def __init__(self, data: bytes, chunk_size: int) -> None:
                self._data = data
                self._pos = 0
                self._chunk_size = chunk_size

            async def read(self, _n: int) -> bytes:
                if self._pos >= len(self._data):
                    return b""
                end = min(self._pos + self._chunk_size, len(self._data))
                buf = self._data[self._pos : end]
                self._pos = end
                return buf

        payload = b"hello-world" * 500
        reader = _Reader(payload, chunk_size=64)
        target = tmp_path / "chunk.tmp"
        length, sha256 = await stream_chunk_to_temp(reader, target, read_chunk_size=64)

        assert length == len(payload)
        assert sha256 == hashlib.sha256(payload).hexdigest()
        assert target.read_bytes() == payload
