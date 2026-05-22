"""
Tests for the rewired TUS handlers (``tus_check_session``, ``tus_upload_part``).

The handlers are exercised against real ``tmp_path`` session directories;
only the volume/context plumbing is mocked. This covers header-level guard
checks (Upload-Offset parsing, range bounds) plus the end-to-end happy path
that writes through to ``TusUploadSession``.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from ai.backend.storage.api.client import tus_upload_part
from ai.backend.storage.errors import InvalidAPIParameters, UploadOffsetMismatchError


@dataclasses.dataclass(slots=True)
class _PatchEnv:
    vfpath: Path
    session_dir: Path


def _build_request(
    *,
    vfpath: Path,
    session_id: str,
    total_size: int,
    body: bytes | None,
    offset_header: str | None,
) -> MagicMock:
    volume = MagicMock()
    volume.mangle_vfpath.return_value = vfpath

    ctx = MagicMock()
    ctx.local_config.storage_proxy.secret = "test-secret"
    ctx.get_volume.return_value.__aenter__ = AsyncMock(return_value=volume)
    ctx.get_volume.return_value.__aexit__ = AsyncMock(return_value=None)

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
def patch_env(tmp_path: Path) -> _PatchEnv:
    session_id = "test-session"
    vfpath = tmp_path / "vfpath"
    session_dir = vfpath / ".upload" / session_id
    session_dir.mkdir(parents=True)
    return _PatchEnv(vfpath=vfpath, session_dir=session_dir)


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
    async def test_missing_offset_header_raises(self, patch_env: _PatchEnv) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id="test-session",
            total_size=1024,
            body=None,
            offset_header=None,
        )
        token_data = _token_data(session_id="test-session", total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(InvalidAPIParameters):
                await tus_upload_part(request)
        finally:
            cp.stop()

    async def test_non_integer_offset_header_raises(self, patch_env: _PatchEnv) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id="test-session",
            total_size=1024,
            body=None,
            offset_header="not-a-number",
        )
        token_data = _token_data(session_id="test-session", total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(InvalidAPIParameters):
                await tus_upload_part(request)
        finally:
            cp.stop()

    async def test_negative_offset_raises_conflict(self, patch_env: _PatchEnv) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id="test-session",
            total_size=1024,
            body=None,
            offset_header="-1",
        )
        token_data = _token_data(session_id="test-session", total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(UploadOffsetMismatchError):
                await tus_upload_part(request)
        finally:
            cp.stop()

    async def test_offset_above_total_size_raises_conflict(self, patch_env: _PatchEnv) -> None:
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id="test-session",
            total_size=1024,
            body=None,
            offset_header="2048",
        )
        token_data = _token_data(session_id="test-session", total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(UploadOffsetMismatchError):
                await tus_upload_part(request)
        finally:
            cp.stop()


class TestSessionNotFound:
    async def test_missing_session_dir_raises_not_found(self, tmp_path: Path) -> None:
        vfpath = tmp_path / "vfpath"
        vfpath.mkdir()
        # NOTE: do not create .upload/<session> — session has not been prepared.

        request = _build_request(
            vfpath=vfpath,
            session_id="missing-session",
            total_size=1024,
            body=b"",
            offset_header="0",
        )
        token_data = _token_data(session_id="missing-session", total_size=1024, relpath="f.bin")
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(web.HTTPNotFound):
                await tus_upload_part(request)
        finally:
            cp.stop()


class TestHappyPath:
    async def test_single_chunk_upload_completes_and_assembles(self, patch_env: _PatchEnv) -> None:
        payload = b"hello world" * 100
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id="test-session",
            total_size=len(payload),
            body=payload,
            offset_header="0",
        )
        token_data = _token_data(
            session_id="test-session",
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
        # Session directory must be cleaned up after assembly.
        assert not patch_env.session_dir.exists()

    async def test_two_chunks_assemble_in_order(self, patch_env: _PatchEnv) -> None:
        token_data = _token_data(session_id="test-session", total_size=2048, relpath="result.bin")

        cp = _patch_handler_params(token_data)
        try:
            first = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=2048,
                body=b"A" * 1024,
                offset_header="0",
            )
            await tus_upload_part(first)

            second = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=2048,
                body=b"B" * 1024,
                offset_header="1024",
            )
            response = await tus_upload_part(second)
        finally:
            cp.stop()

        assert response.headers["Upload-Offset"] == "2048"
        final_path = patch_env.vfpath / "result.bin"
        assert final_path.read_bytes() == b"A" * 1024 + b"B" * 1024

    async def test_duplicate_chunk_replay_is_idempotent(self, patch_env: _PatchEnv) -> None:
        token_data = _token_data(session_id="test-session", total_size=2048, relpath="result.bin")
        cp = _patch_handler_params(token_data)
        try:
            payload = b"A" * 1024
            first = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=2048,
                body=payload,
                offset_header="0",
            )
            await tus_upload_part(first)

            # Replay the same chunk; must not change committed offset.
            replay = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=2048,
                body=payload,
                offset_header="0",
            )
            response = await tus_upload_part(replay)
        finally:
            cp.stop()

        assert response.headers["Upload-Offset"] == "1024"
        # Session is still pending (not finalized).
        assert patch_env.session_dir.exists()

    async def test_chunk_exceeding_declared_size_raises(self, patch_env: _PatchEnv) -> None:
        token_data = _token_data(session_id="test-session", total_size=10, relpath="result.bin")
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id="test-session",
            total_size=10,
            body=b"too-much-data",  # 13 bytes > 10
            offset_header="0",
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
