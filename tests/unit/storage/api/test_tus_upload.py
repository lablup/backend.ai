"""
Tests for the rewired TUS handlers (``tus_check_session``, ``tus_upload_part``).

The handlers run against a real Valkey (the ``valkey_tus_client`` fixture, backed
by a redis container) and ``tmp_path`` chunk storage; only the volume/context
plumbing is mocked. This covers header-level guard checks (Upload-Offset parsing,
range bounds) plus the end-to-end happy path that writes through to
``TusUploadSession``.
"""

from __future__ import annotations

import dataclasses
import secrets
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_tus import ValkeyTusClient
from ai.backend.common.defs import REDIS_TUS_DB
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget
from ai.backend.storage.api.client import tus_upload_part
from ai.backend.storage.errors import InvalidAPIParameters, UploadOffsetMismatchError
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
) -> MagicMock:
    volume = MagicMock()
    volume.mangle_vfpath.return_value = vfpath

    ctx = MagicMock()
    ctx.local_config.storage_proxy.secret = "test-secret"
    ctx.get_volume.return_value.__aenter__ = AsyncMock(return_value=volume)
    ctx.get_volume.return_value.__aexit__ = AsyncMock(return_value=None)
    ctx.valkey_tus_client = valkey_client

    request = MagicMock(spec=web.Request)
    request.app = {"ctx": ctx}
    request.headers = {}
    if offset_header is not None:
        request.headers["Upload-Offset"] = offset_header
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


class TestUploadOffsetHeaderValidation:
    async def test_missing_offset_header_raises(
        self, patch_env: _PatchEnv, valkey_tus_client: ValkeyTusClient
    ) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=1024,
            body=None,
            offset_header=None,
            valkey_client=valkey_tus_client,
        )
        token_data = _token_data(session_id=patch_env.session_id, total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(InvalidAPIParameters):
                await tus_upload_part(request)
        finally:
            cp.stop()

    async def test_non_integer_offset_header_raises(
        self, patch_env: _PatchEnv, valkey_tus_client: ValkeyTusClient
    ) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=1024,
            body=None,
            offset_header="not-a-number",
            valkey_client=valkey_tus_client,
        )
        token_data = _token_data(session_id=patch_env.session_id, total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(InvalidAPIParameters):
                await tus_upload_part(request)
        finally:
            cp.stop()

    async def test_negative_offset_raises_conflict(
        self, patch_env: _PatchEnv, valkey_tus_client: ValkeyTusClient
    ) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=1024,
            body=None,
            offset_header="-1",
            valkey_client=valkey_tus_client,
        )
        token_data = _token_data(session_id=patch_env.session_id, total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(UploadOffsetMismatchError):
                await tus_upload_part(request)
        finally:
            cp.stop()

    async def test_offset_above_total_size_raises_conflict(
        self, patch_env: _PatchEnv, valkey_tus_client: ValkeyTusClient
    ) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=1024,
            body=None,
            offset_header="2048",
            valkey_client=valkey_tus_client,
        )
        token_data = _token_data(session_id=patch_env.session_id, total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(UploadOffsetMismatchError):
                await tus_upload_part(request)
        finally:
            cp.stop()


class TestSessionNotFound:
    async def test_missing_session_dir_raises_not_found(
        self, tmp_path: Path, valkey_tus_client: ValkeyTusClient
    ) -> None:
        vfpath = tmp_path / "vfpath"
        vfpath.mkdir()
        # NOTE: do not create .upload/<session> — session has not been prepared.

        request = _build_request(
            vfpath=vfpath,
            session_id=f"missing-{secrets.token_hex(8)}",
            total_size=1024,
            body=b"",
            offset_header="0",
            valkey_client=valkey_tus_client,
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
        self, patch_env: _PatchEnv, valkey_tus_client: ValkeyTusClient
    ) -> None:
        payload = b"hello world" * 100
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id=patch_env.session_id,
            total_size=len(payload),
            body=payload,
            offset_header="0",
            valkey_client=valkey_tus_client,
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
        self, patch_env: _PatchEnv, valkey_tus_client: ValkeyTusClient
    ) -> None:
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
            )
            await tus_upload_part(first)

            second = _build_request(
                vfpath=patch_env.vfpath,
                session_id=patch_env.session_id,
                total_size=2048,
                body=b"B" * 1024,
                offset_header="1024",
                valkey_client=valkey_tus_client,
            )
            response = await tus_upload_part(second)
        finally:
            cp.stop()

        assert response.headers["Upload-Offset"] == "2048"
        final_path = patch_env.vfpath / "result.bin"
        assert final_path.read_bytes() == b"A" * 1024 + b"B" * 1024

    async def test_duplicate_chunk_replay_is_idempotent(
        self, patch_env: _PatchEnv, valkey_tus_client: ValkeyTusClient
    ) -> None:
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
            )
            response = await tus_upload_part(replay)
        finally:
            cp.stop()

        assert response.headers["Upload-Offset"] == "1024"

    async def test_chunk_exceeding_declared_size_raises(
        self, patch_env: _PatchEnv, valkey_tus_client: ValkeyTusClient
    ) -> None:
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
        )
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(UploadOffsetMismatchError):
                await tus_upload_part(request)
        finally:
            cp.stop()

        # The aborted temp chunk file must be cleaned up.
        chunks_dir = patch_env.session_dir / "chunks"
        if chunks_dir.exists():
            assert list(chunks_dir.glob("*.tmp")) == []
