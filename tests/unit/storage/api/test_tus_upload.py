"""
Tests for the TUS PATCH handler (``tus_upload_part``).

The handler is exercised against real ``tmp_path`` session directories;
only the volume/context plumbing is mocked. This validates both header-level
guard checks (Upload-Offset parsing, range bounds) and the end-to-end happy
path that writes through to ``TusUploadSession``.
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from ai.backend.storage.api.client import tus_upload_part, tus_upload_status
from ai.backend.storage.errors import (
    ChunkChecksumMismatchError,
    InvalidAPIParameters,
    InvalidUploadChecksumHeaderError,
    UploadOffsetMismatchError,
)


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
    checksum_header: str | None = None,
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


def _sha256_b64(data: bytes) -> str:
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")


def _body_bytes(response: web.Response) -> bytes:
    body = response.body
    assert isinstance(body, (bytes, bytearray))
    return bytes(body)


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


class TestProgressHeaders:
    async def test_patch_response_includes_progress_headers(self, patch_env: _PatchEnv) -> None:
        token_data = _token_data(session_id="test-session", total_size=2048, relpath="result.bin")
        cp = _patch_handler_params(token_data)
        try:
            request = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=2048,
                body=b"A" * 1024,
                offset_header="0",
            )
            response = await tus_upload_part(request)
        finally:
            cp.stop()

        assert response.headers["X-Backend-Ai-Chunks-Received"] == "1"
        assert response.headers["X-Backend-Ai-Total-Expected"] == "2048"
        assert response.headers["X-Backend-Ai-Progress-Percent"] == "50.0"


class TestUploadChecksum:
    async def test_matching_checksum_accepted(self, patch_env: _PatchEnv) -> None:
        payload = b"X" * 1024
        token_data = _token_data(session_id="test-session", total_size=1024, relpath="result.bin")
        cp = _patch_handler_params(token_data)
        try:
            request = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=1024,
                body=payload,
                offset_header="0",
                checksum_header=f"sha256 {_sha256_b64(payload)}",
            )
            response = await tus_upload_part(request)
        finally:
            cp.stop()
        assert response.headers["Upload-Offset"] == "1024"
        assert (patch_env.vfpath / "result.bin").read_bytes() == payload

    async def test_mismatched_checksum_rejected(self, patch_env: _PatchEnv) -> None:
        payload = b"X" * 1024
        wrong = _sha256_b64(b"different-payload")
        token_data = _token_data(session_id="test-session", total_size=1024, relpath="result.bin")
        cp = _patch_handler_params(token_data)
        try:
            request = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=1024,
                body=payload,
                offset_header="0",
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
        self, patch_env: _PatchEnv, header: str
    ) -> None:
        token_data = _token_data(session_id="test-session", total_size=1024, relpath="result.bin")
        cp = _patch_handler_params(token_data)
        try:
            request = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=1024,
                body=b"X" * 1024,
                offset_header="0",
                checksum_header=header,
            )
            with pytest.raises(InvalidUploadChecksumHeaderError):
                await tus_upload_part(request)
        finally:
            cp.stop()


class TestUploadStatus:
    async def test_status_for_empty_session(self, patch_env: _PatchEnv) -> None:
        token_data = _token_data(session_id="test-session", total_size=2048, relpath="result.bin")
        request = _build_request(
            vfpath=patch_env.vfpath,
            session_id="test-session",
            total_size=2048,
            body=None,
            offset_header=None,
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
        assert payload["status"] == "pending"

    async def test_status_after_partial_upload(self, patch_env: _PatchEnv) -> None:
        token_data = _token_data(session_id="test-session", total_size=4096, relpath="result.bin")
        cp = _patch_handler_params(token_data)
        try:
            patch_request = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=4096,
                body=b"A" * 1024,
                offset_header="0",
            )
            await tus_upload_part(patch_request)

            status_request = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=4096,
                body=None,
                offset_header=None,
            )
            response = await tus_upload_status(status_request)
        finally:
            cp.stop()

        payload = json.loads(_body_bytes(response))
        assert payload["committed_offset"] == 1024
        assert payload["chunks_received"] == [0]
        assert payload["missing_ranges"] == [{"offset": 1024, "length": 3072}]
        assert payload["progress_percent"] == 25.0
        assert payload["status"] == "pending"

    async def test_status_with_out_of_order_chunks_reports_gaps(self, patch_env: _PatchEnv) -> None:
        token_data = _token_data(session_id="test-session", total_size=4096, relpath="result.bin")
        cp = _patch_handler_params(token_data)
        try:
            # Commit the *second* chunk first, leaving [0, 1024) missing.
            second = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=4096,
                body=b"B" * 1024,
                offset_header="1024",
            )
            await tus_upload_part(second)

            status_request = _build_request(
                vfpath=patch_env.vfpath,
                session_id="test-session",
                total_size=4096,
                body=None,
                offset_header=None,
            )
            response = await tus_upload_status(status_request)
        finally:
            cp.stop()

        payload = json.loads(_body_bytes(response))
        # The contiguous prefix has not advanced because [0,1024) is missing.
        assert payload["committed_offset"] == 0
        assert payload["chunks_received"] == [1024]
        assert payload["missing_ranges"] == [
            {"offset": 0, "length": 1024},
            {"offset": 2048, "length": 2048},
        ]

    async def test_status_for_missing_session_returns_404(self, tmp_path: Path) -> None:
        vfpath = tmp_path / "vfpath"
        vfpath.mkdir()
        token_data = _token_data(session_id="missing", total_size=1024, relpath="result.bin")
        request = _build_request(
            vfpath=vfpath,
            session_id="missing",
            total_size=1024,
            body=None,
            offset_header=None,
        )
        cp = _patch_handler_params(token_data)
        try:
            with pytest.raises(web.HTTPNotFound):
                await tus_upload_status(request)
        finally:
            cp.stop()
