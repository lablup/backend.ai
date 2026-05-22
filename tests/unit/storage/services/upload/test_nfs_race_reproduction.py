"""
BA-3974 — multi-proxy NFS race condition reproduction.

This file does two things:

1. Reconstructs the *pre-PR* upload model (single temp file, ``stat()`` to
   discover position, then append) and shows it CORRUPTS data when two or
   more workers race — without needing a real NFS mount.

2. Drives the *new* metadata-driven model under the exact same chaos and
   confirms the assembled output is byte-perfect.

How the NFS race is faked on a local filesystem
-----------------------------------------------
On NFS, two things conspire to break the old append model:

  (a) Each NFS client caches file attributes (``st_size`` in particular).
      Two storage-proxy replicas calling ``stat()`` close together can
      both see the same cached "end of file" value, even though writes
      from the other replica are already in flight.

  (b) NFS does not give cross-client ``O_APPEND`` atomicity. Each client
      issues a positioned write based on its cached size, and the writes
      do NOT serialize at the byte level the way they do on a local
      kernel.

Linux on local ext4 makes both go away — ``stat()`` is always coherent and
``O_APPEND`` writes are atomic. To expose the bug in a unit test we replace
both behaviors:

  (a) is faked by ``unittest.mock.patch`` on ``pathlib.Path.stat`` to
      return a frozen snapshot for the upload temp file.
  (b) is faked by using ``os.lseek`` + ``os.write`` (no ``O_APPEND``).

Under that combination, the old offset-check guard from BA-3678 passes
for every concurrent worker — they all observe the same stale ``st_size``
— and they all race to write at the same byte position, clobbering each
other. That is exactly the corruption pattern reported on production
multi-proxy + shared NFS deployments.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest

from ai.backend.common.clients.valkey_client.valkey_tus import ValkeyTusClient
from ai.backend.common.lock import DistributedLockFactory
from ai.backend.common.types import TusSessionId
from ai.backend.storage.services.upload.tus_session import TusUploadSession
from ai.backend.storage.services.upload.types import TusUploadSessionArgs

# -----------------------------------------------------------------------------
# Legacy model reconstruction
# -----------------------------------------------------------------------------


class _FakeStat:
    """A minimal ``stat_result`` stand-in (only ``st_size`` is used)."""

    __slots__ = ("st_size",)

    def __init__(self, st_size: int) -> None:
        self.st_size = st_size


def _legacy_upload_chunk(file_path: Path, expected_offset: int, payload: bytes) -> str:
    """
    Distilled reconstruction of the pre-PR ``tus_upload_part`` body:

        actual = file_path.stat().st_size
        if actual != expected_offset:
            raise UploadOffsetMismatchError(...)
        # AsyncFileWriter(access_mode="ab"): append the chunk

    Critically, we use ``os.lseek`` + ``os.write`` here rather than the real
    ``O_APPEND``-backed writer, because that is what NFS effectively does
    across clients: the kernel cannot serialize positions across hosts, so
    a write lands at the offset the client computed from its own cached
    view of the file size.
    """
    actual = file_path.stat().st_size
    if actual != expected_offset:
        return "offset-mismatch"
    fd = os.open(file_path, os.O_WRONLY)
    try:
        os.lseek(fd, actual, os.SEEK_SET)
        os.write(fd, payload)
    finally:
        os.close(fd)
    return "wrote"


# -----------------------------------------------------------------------------
# Test scenario shared between legacy and new models
# -----------------------------------------------------------------------------


CHUNK_SIZE = 64 * 1024
NUM_CHUNKS = 8
TOTAL_SIZE = CHUNK_SIZE * NUM_CHUNKS


@pytest.fixture
def random_chunks() -> list[bytes]:
    rng = secrets.SystemRandom()
    return [bytes(rng.randbytes(CHUNK_SIZE)) for _ in range(NUM_CHUNKS)]


# -----------------------------------------------------------------------------
# 1) Legacy model demonstrably corrupts under NFS-like stale stat
# -----------------------------------------------------------------------------


class TestLegacyModelCorruptsUnderStaleStatCache:
    def test_concurrent_writes_clobber_each_other(
        self, tmp_path: Path, random_chunks: list[bytes]
    ) -> None:
        upload_path = tmp_path / "upload.bin"
        upload_path.touch()

        # All concurrent workers will see this frozen value, mirroring NFS
        # attribute cache staleness across clients.
        stale = _FakeStat(st_size=0)

        original_stat = Path.stat

        def fake_stat(self: Path, *, follow_symlinks: bool = True) -> object:
            if self == upload_path:
                return stale
            return original_stat(self, follow_symlinks=follow_symlinks)

        # Force all workers to start at the same instant so they all
        # observe the empty-file snapshot together.
        barrier = threading.Barrier(NUM_CHUNKS)

        def worker(payload: bytes) -> str:
            barrier.wait()
            return _legacy_upload_chunk(upload_path, 0, payload)

        with patch.object(Path, "stat", fake_stat):
            with ThreadPoolExecutor(max_workers=NUM_CHUNKS) as pool:
                results = list(pool.map(worker, random_chunks))

        # The post-BA-3678 offset guard passes for *every* worker because
        # they all see st_size = 0. None are rejected.
        assert all(r == "wrote" for r in results), (
            f"expected every worker to pass the offset check, got {results}"
        )

        # The on-disk file CANNOT match a correct concatenation of all
        # chunks — every write went to position 0.
        expected = b"".join(random_chunks)
        actual = upload_path.read_bytes()
        assert actual != expected, (
            "test setup failure: legacy model unexpectedly produced the "
            "correct output (race window did not open)"
        )

        # File length should be at most one chunk's worth of bytes,
        # because every writer started at position 0 and overlapped.
        # On a healthy upload it would be NUM_CHUNKS * CHUNK_SIZE.
        assert len(actual) <= CHUNK_SIZE, (
            f"corrupted file should be at most {CHUNK_SIZE} bytes, "
            f"got {len(actual)} (expected correct length "
            f"{TOTAL_SIZE} on a non-broken model)"
        )

    def test_legacy_guard_does_not_help_when_two_workers_see_same_size(
        self, tmp_path: Path
    ) -> None:
        """
        Even with the BA-3678 offset guard, two workers that race past the
        guard cause corruption. Proves the guard fixes single-client
        ordering only, not multi-proxy concurrency.
        """
        upload_path = tmp_path / "upload.bin"
        upload_path.write_bytes(b"\x00" * CHUNK_SIZE)  # 1 chunk already there

        # NFS-like stale cache: both workers see size = CHUNK_SIZE.
        stale = _FakeStat(st_size=CHUNK_SIZE)
        original_stat = Path.stat

        def fake_stat(self: Path, *, follow_symlinks: bool = True) -> object:
            if self == upload_path:
                return stale
            return original_stat(self, follow_symlinks=follow_symlinks)

        a = b"A" * CHUNK_SIZE
        b = b"B" * CHUNK_SIZE
        barrier = threading.Barrier(2)

        def worker(payload: bytes) -> str:
            barrier.wait()
            # Both pass `expected_offset=CHUNK_SIZE` (correct per their view).
            return _legacy_upload_chunk(upload_path, CHUNK_SIZE, payload)

        with patch.object(Path, "stat", fake_stat):
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(worker, [a, b]))

        # Both passed the guard.
        assert results == ["wrote", "wrote"]

        # File contents at position CHUNK_SIZE onwards is either all A or
        # all B — never the correct A-then-B concatenation. Both writers
        # claimed the same range.
        contents = upload_path.read_bytes()
        assert len(contents) == 2 * CHUNK_SIZE
        chunk2 = contents[CHUNK_SIZE:]
        # One writer clobbered the other: the slot holds a single writer's
        # bytes, never a clean A-then-B concatenation — so one chunk is lost.
        assert chunk2 in (a, b), (
            "byte-interleaving acceptable, but at minimum chunk2 must come "
            "from a single writer (not a clean concatenation of both)"
        )


# -----------------------------------------------------------------------------
# 2) New model survives the same chaos
# -----------------------------------------------------------------------------


class TestNewModelSurvivesSameChaos:
    async def test_concurrent_chunks_assemble_byte_perfect(
        self,
        tmp_path: Path,
        random_chunks: list[bytes],
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        """
        Drive ``TusUploadSession`` with the same workload pattern as the
        legacy test above — NUM_CHUNKS workers, all firing at once — and
        confirm the assembled output equals the original payload, bit for
        bit.
        """
        session = TusUploadSession(
            TusUploadSessionArgs(
                session_dir=tmp_path / "sess",
                session_id=TusSessionId(secrets.token_hex(8)),
                total_size=TOTAL_SIZE,
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
        )
        await session.ensure_initialized()

        async def commit_chunk(idx: int) -> None:
            offset = idx * CHUNK_SIZE
            payload = random_chunks[idx]
            temp = session.open_temp_chunk(offset)
            temp.write_bytes(payload)
            await session.commit_chunk(
                offset=offset,
                chunk_path=temp,
                length=CHUNK_SIZE,
                sha256=hashlib.sha256(payload).hexdigest(),
            )

        await asyncio.gather(*(commit_chunk(i) for i in range(NUM_CHUNKS)))

        target = tmp_path / "out.bin"
        await session.assemble(target)
        await session.cleanup()

        expected = b"".join(random_chunks)
        actual = target.read_bytes()
        assert actual == expected, "assembled file diverges from source payload"
        assert hashlib.sha256(actual).hexdigest() == hashlib.sha256(expected).hexdigest()

    async def test_duplicate_retries_under_chaos_remain_idempotent(
        self,
        tmp_path: Path,
        random_chunks: list[bytes],
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        """
        Each chunk is fired THREE times concurrently — modeling a retry
        storm where the original request is still in flight to one proxy
        while two replicas of it arrive at others. The assembled file
        must still equal the original payload.
        """
        session = TusUploadSession(
            TusUploadSessionArgs(
                session_dir=tmp_path / "sess",
                session_id=TusSessionId(secrets.token_hex(8)),
                total_size=TOTAL_SIZE,
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
        )
        await session.ensure_initialized()

        async def commit_chunk(idx: int) -> bool:
            offset = idx * CHUNK_SIZE
            payload = random_chunks[idx]
            temp = session.open_temp_chunk(offset)
            temp.write_bytes(payload)
            acc = await session.commit_chunk(
                offset=offset,
                chunk_path=temp,
                length=CHUNK_SIZE,
                sha256=hashlib.sha256(payload).hexdigest(),
            )
            return acc.committed

        # 3 replicas of every chunk → 3 * NUM_CHUNKS concurrent tasks.
        tasks = [commit_chunk(i) for i in range(NUM_CHUNKS) for _ in range(3)]
        committed_flags = await asyncio.gather(*tasks)

        committed = sum(1 for c in committed_flags if c)
        replays = sum(1 for c in committed_flags if not c)
        assert committed == NUM_CHUNKS, f"exactly one commit per offset should win, got {committed}"
        assert replays == NUM_CHUNKS * 2

        target = tmp_path / "out.bin"
        await session.assemble(target)
        await session.cleanup()
        assert target.read_bytes() == b"".join(random_chunks)
