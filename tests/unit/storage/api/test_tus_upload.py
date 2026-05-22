"""
Tests for the rewired TUS handlers (``tus_check_session``, ``tus_upload_part``).

The handlers run against a real Valkey (the ``valkey_tus_client`` fixture, backed
by a redis container) and ``tmp_path`` chunk storage; only the volume/context
plumbing is mocked. This covers header-level guard checks (Upload-Offset parsing,
range bounds) plus the end-to-end happy path that writes through to
``TusUploadSession``.
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import secrets
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from redis.asyncio import Redis

from ai.backend.common import config
from ai.backend.common.clients.valkey_client.valkey_tus import ValkeyTusClient
from ai.backend.common.defs import REDIS_STREAM_LOCK, REDIS_TUS_DB
from ai.backend.common.lock import DistributedLockFactory
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import RedisConnectionInfo, TusSessionId, ValkeyTarget
from ai.backend.storage.api.client import tus_upload_part, tus_upload_status
from ai.backend.storage.errors import (
    ChunkChecksumMismatchError,
    InvalidAPIParameters,
    InvalidUploadChecksumHeaderError,
    UploadChunkExceedsTotalSizeError,
    UploadOffsetMismatchError,
)
from ai.backend.storage.services.upload.lock import create_tus_lock_factory
from ai.backend.storage.services.upload.types import TusSessionState
from ai.backend.testutils.bootstrap import redis_container  # noqa: F401


@pytest.fixture
async def valkey_tus_client(
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> AsyncIterator[ValkeyTusClient]:
    hostport_pair = redis_container[1]
    client = await ValkeyTusClient.create(
        ValkeyTarget(addr=hostport_pair.address),
        db_id=REDIS_TUS_DB,
        human_readable_name="test.tus.api",
    )
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
async def tus_lock_factory(
    redis_container: tuple[str, HostPortPairModel],  # noqa: F811
) -> AsyncIterator[DistributedLockFactory]:
    hostport_pair = redis_container[1]
    lock_redis = RedisConnectionInfo(
        Redis.from_url(f"redis://{hostport_pair.address}/{REDIS_STREAM_LOCK}"),
        sentinel=None,
        name="test.tus.api.lock",
        service_name=None,
        redis_helper_config=config.redis_helper_default_config,
    )
    try:
        yield create_tus_lock_factory(lock_redis)
    finally:
        await lock_redis.close()


@dataclasses.dataclass(slots=True)
class _PatchEnv:
    vfpath: Path
    session_dir: Path
    session_id: str


def _build_request(
    *,
    vfpath: Path,
    session_id: str,
    total_size: int,
    body: bytes | None,
    offset_header: str | None,
    valkey_client: ValkeyTusClient,
    lock_factory: DistributedLockFactory,
    checksum_header: str | None = None,
) -> MagicMock:
    volume = MagicMock()
    volume.mangle_vfpath.return_value = vfpath

    ctx = MagicMock()
    ctx.local_config.storage_proxy.secret = "test-secret"
    ctx.get_volume.return_value.__aenter__ = AsyncMock(return_value=volume)
    ctx.get_volume.return_value.__aexit__ = AsyncMock(return_value=None)
    ctx.valkey_tus_client = valkey_client
    ctx.tus_lock_factory = lock_factory

    request = MagicMock(spec=web.Request)
    request.app = {"ctx": ctx}
    request.headers = {}
    if offset_header is not None:
        request.headers["Upload-Offset"] = offset_header
    if checksum_header is not None:
        request.headers["Upload-Checksum"] = checksum_header
    request.query = {"token": "test-token"}

    if body is None:
        content = AsyncMock()
        content.read = AsyncMock(return_value=b"")
        request.content = content
    else:
        body_state = {"pos": 0}

        async def _read(_n: int) -> bytes:
            if body_state["pos"] >= len(body):
                return b""
            chunk = body[body_state["pos"] :]
            body_state["pos"] = len(body)
            return chunk

        content = AsyncMock()
        content.read = AsyncMock(side_effect=_read)
        request.content = content

    return request


@pytest.fixture
def tus_session_id() -> str:
    # Unique per test so each test is isolated within the shared Valkey.
    return f"test-session-{secrets.token_hex(8)}"


@pytest.fixture
def patch_env(tmp_path: Path, tus_session_id: str) -> _PatchEnv:
    vfpath = tmp_path / "vfpath"
    session_dir = vfpath / ".upload" / tus_session_id
    session_dir.mkdir(parents=True)
    return _PatchEnv(vfpath=vfpath, session_dir=session_dir, session_id=tus_session_id)


def _token_data(*, session_id: str, total_size: int, relpath: str) -> dict[str, Any]:
    return {
        "volume": "test-volume",
        "vfid": MagicMock(),
        "session": session_id,
        "size": total_size,
        "relpath": relpath,
    }


def _patch_handler_params(token_data: dict[str, Any]) -> Any:
    cp = patch("ai.backend.storage.api.client.check_params")
    mock_check_params = cp.start()
    mock_check_params.return_value.__aenter__ = AsyncMock(
        return_value={"token": token_data, "dst_dir": None}
    )
    mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
    return cp


async def _register_session_state(
    valkey: ValkeyTusClient, session_id: str, total_size: int
) -> None:
    """Mimic ``create_upload_session`` having pre-registered the session in Valkey."""
    sid = TusSessionId(session_id)
    await valkey.set_session_state(sid, TusSessionState.empty(sid, total_size).model_dump_json())


class TestUploadOffsetHeaderValidation:
    async def test_missing_offset_header_raises(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=1024,
            body=None,
            offset_header=None,
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
        token_data = _token_data(session_id=patch_env.session_id, total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(InvalidAPIParameters):
                await tus_upload_part(request)
        finally:
            cp.stop()

    async def test_non_integer_offset_header_raises(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=1024,
            body=None,
            offset_header="not-a-number",
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
        token_data = _token_data(session_id=patch_env.session_id, total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(InvalidAPIParameters):
                await tus_upload_part(request)
        finally:
            cp.stop()

    async def test_negative_offset_raises_conflict(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=1024,
            body=None,
            offset_header="-1",
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
        token_data = _token_data(session_id=patch_env.session_id, total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(UploadOffsetMismatchError):
                await tus_upload_part(request)
        finally:
            cp.stop()

    async def test_offset_above_total_size_raises_conflict(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=1024,
            body=None,
            offset_header="2048",
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
        token_data = _token_data(session_id=patch_env.session_id, total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(UploadOffsetMismatchError):
                await tus_upload_part(request)
        finally:
            cp.stop()


class TestSessionNotFound:
    async def test_missing_valkey_state_raises_not_found(
        self,
        tmp_path: Path,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        # The session has never been registered in Valkey (no
        # `create_upload_session` call). Existence is determined by the Valkey
        # state, so the handler must 404 regardless of any filesystem layout.
        vfpath = tmp_path / "vfpath"
        vfpath.mkdir()

        request = _build_request(
            vfpath=vfpath,
            session_id=f"missing-{secrets.token_hex(8)}",
            total_size=1024,
            body=b"",
            offset_header="0",
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
        token_data = _token_data(session_id="missing-session", total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(web.HTTPNotFound):
                await tus_upload_part(request)
        finally:
            cp.stop()


class TestHappyPath:
    async def test_single_chunk_upload_completes_and_assembles(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        payload = b"hello world" * 100
        await _register_session_state(valkey_tus_client, patch_env.session_id, len(payload))
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=len(payload),
            body=payload,
            offset_header="0",
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
        token_data = _token_data(
            session_id=patch_env.session_id,
            total_size=len(payload),
            relpath="result.bin",
        )
        cp = _patch_handler_params(token_data)
        try:
            response = await tus_upload_part(request)
        finally:
            cp.stop()

        assert response.headers["Upload-Offset"] == str(len(payload))
        final_path = patch_env.vfpath / "result.bin"
        assert final_path.read_bytes() == payload
        # After assembly the chunk payloads are reclaimed; the completed marker
        # is kept in Valkey (so a late duplicate PATCH observes completion).
        assert list((patch_env.session_dir / "chunks").glob("*.dat")) == []

    async def test_two_chunks_assemble_in_order(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        await _register_session_state(valkey_tus_client, patch_env.session_id, 2048)
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=2048, relpath="result.bin"
        )

        cp = _patch_handler_params(token_data)
        try:
            first = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=2048,
                body=b"A" * 1024,
                offset_header="0",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
            await tus_upload_part(first)

            second = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=2048,
                body=b"B" * 1024,
                offset_header="1024",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
            response = await tus_upload_part(second)
        finally:
            cp.stop()

        assert response.headers["Upload-Offset"] == "2048"
        final_path = patch_env.vfpath / "result.bin"
        assert final_path.read_bytes() == b"A" * 1024 + b"B" * 1024

    async def test_duplicate_chunk_replay_is_idempotent(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        await _register_session_state(valkey_tus_client, patch_env.session_id, 2048)
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=2048, relpath="result.bin"
        )
        cp = _patch_handler_params(token_data)
        try:
            payload = b"A" * 1024
            first = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=2048,
                body=payload,
                offset_header="0",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
            await tus_upload_part(first)

            # Replay the same chunk; must not change committed offset.
            replay = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=2048,
                body=payload,
                offset_header="0",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
            response = await tus_upload_part(replay)
        finally:
            cp.stop()

        assert response.headers["Upload-Offset"] == "1024"

    async def test_chunk_exceeding_declared_size_raises(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        await _register_session_state(valkey_tus_client, patch_env.session_id, 10)
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=10, relpath="result.bin"
        )
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=10,
            body=b"too-much-data",  # 13 bytes > 10
            offset_header="0",
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(UploadChunkExceedsTotalSizeError):
                await tus_upload_part(request)
        finally:
            cp.stop()

        # The aborted temp chunk file must be cleaned up.
        chunks_dir = patch_env.session_dir / "chunks"
        if chunks_dir.exists():
            assert list(chunks_dir.glob("*.tmp")) == []


def _sha256_b64(data: bytes) -> str:
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")


class TestUploadChecksum:
    async def test_matching_checksum_accepted(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        payload = b"X" * 1024
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=1024, relpath="result.bin"
        )
        cp = _patch_handler_params(token_data)
        try:
            request = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=1024,
                body=payload,
                offset_header="0",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
                checksum_header=f"sha256 {_sha256_b64(payload)}",
            )
            response = await tus_upload_part(request)
        finally:
            cp.stop()
        assert response.headers["Upload-Offset"] == "1024"
        assert (patch_env.vfpath / "result.bin").read_bytes() == payload

    async def test_mismatched_checksum_rejected(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        payload = b"X" * 1024
        wrong = _sha256_b64(b"different-payload")
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=1024, relpath="result.bin"
        )
        cp = _patch_handler_params(token_data)
        try:
            request = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=1024,
                body=payload,
                offset_header="0",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
                checksum_header=f"sha256 {wrong}",
            )
            with pytest.raises(ChunkChecksumMismatchError):
                await tus_upload_part(request)
        finally:
            cp.stop()

        # The mismatched chunk must not be committed.
        assert not (patch_env.vfpath / "result.bin").exists()
        chunks_dir = patch_env.session_dir / "chunks"
        if chunks_dir.exists():
            assert list(chunks_dir.glob("*")) == []

    @pytest.mark.parametrize(
        "header",
        [
            "sha256",  # missing digest
            "sha1 abc",  # unsupported algorithm
            "sha256 not_base64!!",  # invalid base64
            "sha256 " + base64.b64encode(b"too-short").decode("ascii"),  # wrong length
        ],
    )
    async def test_malformed_checksum_header_rejected(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
        header: str,
    ) -> None:
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=1024, relpath="result.bin"
        )
        cp = _patch_handler_params(token_data)
        try:
            request = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=1024,
                body=b"X" * 1024,
                offset_header="0",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
                checksum_header=header,
            )
            with pytest.raises(InvalidUploadChecksumHeaderError):
                await tus_upload_part(request)
        finally:
            cp.stop()


def _body_bytes(response: web.Response) -> bytes:
    body = response.body
    assert isinstance(body, (bytes, bytearray))
    return bytes(body)


class TestProgressHeaders:
    async def test_patch_response_includes_progress_headers(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        await _register_session_state(valkey_tus_client, patch_env.session_id, 2048)
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=2048, relpath="result.bin"
        )
        cp = _patch_handler_params(token_data)
        try:
            request = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=2048,
                body=b"A" * 1024,
                offset_header="0",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
            response = await tus_upload_part(request)
        finally:
            cp.stop()

        assert response.headers["X-Backend-Ai-Chunks-Received"] == "1"
        assert response.headers["X-Backend-Ai-Total-Expected"] == "2048"
        assert response.headers["X-Backend-Ai-Progress-Percent"] == "50.0"


class TestUploadStatus:
    async def test_status_for_empty_session(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        await _register_session_state(valkey_tus_client, patch_env.session_id, 2048)
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=2048, relpath="result.bin"
        )
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=2048,
            body=None,
            offset_header=None,
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
        cp = _patch_handler_params(token_data)
        try:
            response = await tus_upload_status(request)
        finally:
            cp.stop()

        payload = json.loads(_body_bytes(response))
        assert payload["total_size"] == 2048
        assert payload["committed_offset"] == 0
        assert payload["chunks_received"] == []
        assert payload["missing_ranges"] == [{"offset": 0, "length": 2048}]
        assert payload["progress_percent"] == 0.0
        assert payload["status"] == "in_progress"

    async def test_status_after_partial_upload(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        await _register_session_state(valkey_tus_client, patch_env.session_id, 4096)
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=4096, relpath="result.bin"
        )
        cp = _patch_handler_params(token_data)
        try:
            patch_request = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=4096,
                body=b"A" * 1024,
                offset_header="0",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
            await tus_upload_part(patch_request)

            status_request = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=4096,
                body=None,
                offset_header=None,
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
            response = await tus_upload_status(status_request)
        finally:
            cp.stop()

        payload = json.loads(_body_bytes(response))
        assert payload["committed_offset"] == 1024
        assert payload["chunks_received"] == [0]
        assert payload["missing_ranges"] == [{"offset": 1024, "length": 3072}]
        assert payload["progress_percent"] == 25.0
        assert payload["status"] == "in_progress"

    async def test_status_with_out_of_order_chunks_reports_gaps(
        self,
        patch_env: _PatchEnv,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        await _register_session_state(valkey_tus_client, patch_env.session_id, 4096)
        token_data = _token_data(
            session_id=patch_env.session_id, total_size=4096, relpath="result.bin"
        )
        cp = _patch_handler_params(token_data)
        try:
            # Commit the *second* chunk first, leaving [0, 1024) missing.
            second = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=4096,
                body=b"B" * 1024,
                offset_header="1024",
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
            await tus_upload_part(second)

            status_request = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=4096,
                body=None,
                offset_header=None,
                valkey_client=valkey_tus_client,
                lock_factory=tus_lock_factory,
            )
            response = await tus_upload_status(status_request)
        finally:
            cp.stop()

        payload = json.loads(_body_bytes(response))
        # Contiguous prefix has not advanced because [0,1024) is missing.
        assert payload["committed_offset"] == 0
        assert payload["chunks_received"] == [1024]
        assert payload["missing_ranges"] == [
            {"offset": 0, "length": 1024},
            {"offset": 2048, "length": 2048},
        ]

    async def test_status_for_missing_session_returns_404(
        self,
        tmp_path: Path,
        valkey_tus_client: ValkeyTusClient,
        tus_lock_factory: DistributedLockFactory,
    ) -> None:
        vfpath = tmp_path / "vfpath"
        vfpath.mkdir()
        missing_id = f"missing-{secrets.token_hex(8)}"
        token_data = _token_data(session_id=missing_id, total_size=1024, relpath="result.bin")
        request = _build_request(
            vfpath=vfpath,
            session_id=missing_id,
            total_size=1024,
            body=None,
            offset_header=None,
            valkey_client=valkey_tus_client,
            lock_factory=tus_lock_factory,
        )
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(web.HTTPNotFound):
                await tus_upload_status(request)
        finally:
            cp.stop()
