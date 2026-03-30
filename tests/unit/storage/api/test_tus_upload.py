"""
Tests for TUS upload offset validation in tus_upload_part().
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from ai.backend.storage.api.client import tus_upload_part
from ai.backend.storage.errors import InvalidAPIParameters, UploadOffsetMismatchError


class TestTusUploadPartOffsetValidation:
    """Tests for Upload-Offset header validation in tus_upload_part()."""

    # =========================================================================
    # Low-level fixtures (internal building blocks)
    # =========================================================================

    @pytest.fixture
    def token_data(self) -> dict[str, Any]:
        """Create mock token data."""
        return {
            "volume": "test-volume",
            "vfid": MagicMock(),
            "session": "test-session",
            "size": "10240",
            "relpath": "test-file.txt",
        }

    def _create_mock_request(
        self,
        tmp_path: Path,
        client_offset: str | None,
    ) -> MagicMock:
        """Create a fully configured mock request."""
        # Mock volume
        volume = MagicMock()
        volume.mangle_vfpath.return_value = tmp_path

        # Mock context
        ctx = MagicMock()
        ctx.local_config.storage_proxy.secret = "test-secret"
        ctx.get_volume.return_value.__aenter__ = AsyncMock(return_value=volume)
        ctx.get_volume.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock request
        request = MagicMock(spec=web.Request)
        request.app = {"ctx": ctx}
        request.headers = {}
        request.query = {"token": "test-token"}

        if client_offset is not None:
            request.headers["Upload-Offset"] = client_offset

        # Mock content reader (returns EOF immediately)
        content = AsyncMock()
        content.at_eof.return_value = True
        request.content = content

        return request

    # =========================================================================
    # Scenario fixtures (composed, one per test scenario)
    # =========================================================================

    @pytest.fixture
    def request_without_offset_header(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Missing Upload-Offset header."""
        request = self._create_mock_request(tmp_path, client_offset=None)

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            yield request

    @pytest.fixture
    def request_with_invalid_offset(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Invalid (non-integer) Upload-Offset header."""
        request = self._create_mock_request(tmp_path, client_offset="not-a-number")

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            yield request

    @pytest.fixture
    def request_offset_mismatch_client_behind(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Client offset (512) behind server offset (1024)."""
        request = self._create_mock_request(tmp_path, client_offset="512")

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            yield request

    @pytest.fixture
    def request_offset_mismatch_client_ahead(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Client offset (2048) ahead of server offset (1024)."""
        request = self._create_mock_request(tmp_path, client_offset="2048")

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            yield request

    @pytest.fixture
    def request_with_matching_offset(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: Client offset matches server offset (both 1024)."""
        request = self._create_mock_request(tmp_path, client_offset="1024")

        # Create upload temp file
        upload_parent = tmp_path / ".upload"
        upload_parent.mkdir(parents=True, exist_ok=True)
        temp_file = upload_parent / token_data["session"]
        temp_file.write_bytes(b"x" * 1024)

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
            patch("ai.backend.storage.api.client.AsyncFileWriter") as mock_writer,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "1024"}

            writer = AsyncMock()
            mock_writer.return_value.__aenter__ = AsyncMock(return_value=writer)
            mock_writer.return_value.__aexit__ = AsyncMock(return_value=None)

            yield request

    @pytest.fixture
    def request_with_zero_offset(
        self, tmp_path: Path, token_data: dict[str, Any]
    ) -> Generator[MagicMock, None, None]:
        """Scenario: New file upload with zero offset."""
        request = self._create_mock_request(tmp_path, client_offset="0")

        # Create empty upload temp file
        upload_parent = tmp_path / ".upload"
        upload_parent.mkdir(parents=True, exist_ok=True)
        temp_file = upload_parent / token_data["session"]
        temp_file.write_bytes(b"")

        with (
            patch("ai.backend.storage.api.client.check_params") as mock_check_params,
            patch("ai.backend.storage.api.client.prepare_tus_session_headers") as mock_headers,
            patch("ai.backend.storage.api.client.AsyncFileWriter") as mock_writer,
        ):
            mock_check_params.return_value.__aenter__ = AsyncMock(
                return_value={"token": token_data, "dst_dir": None}
            )
            mock_check_params.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_headers.return_value = {"Upload-Offset": "0"}

            writer = AsyncMock()
            mock_writer.return_value.__aenter__ = AsyncMock(return_value=writer)
            mock_writer.return_value.__aexit__ = AsyncMock(return_value=None)

            yield request

    # =========================================================================
    # Test methods (minimal fixture injection, Act & Assert only)
    # =========================================================================

    async def test_missing_upload_offset_header_raises_bad_request(
        self,
        request_without_offset_header: MagicMock,
    ) -> None:
        """When Upload-Offset header is missing, should raise InvalidAPIParameters (400)."""
        with pytest.raises(InvalidAPIParameters):
            await tus_upload_part(request_without_offset_header)

    async def test_invalid_upload_offset_header_raises_bad_request(
        self,
        request_with_invalid_offset: MagicMock,
    ) -> None:
        """When Upload-Offset header is not a valid integer, should raise InvalidAPIParameters (400)."""
        with pytest.raises(InvalidAPIParameters):
            await tus_upload_part(request_with_invalid_offset)

    async def test_offset_mismatch_client_behind_raises_conflict(
        self,
        request_offset_mismatch_client_behind: MagicMock,
    ) -> None:
        """When client offset is behind server file size, should raise UploadOffsetMismatchError (409)."""
        with pytest.raises(UploadOffsetMismatchError):
            await tus_upload_part(request_offset_mismatch_client_behind)

    async def test_offset_mismatch_client_ahead_raises_conflict(
        self,
        request_offset_mismatch_client_ahead: MagicMock,
    ) -> None:
        """When client offset is ahead of server file size, should raise UploadOffsetMismatchError (409)."""
        with pytest.raises(UploadOffsetMismatchError):
            await tus_upload_part(request_offset_mismatch_client_ahead)

    async def test_matching_offset_proceeds_with_upload(
        self,
        request_with_matching_offset: MagicMock,
    ) -> None:
        """When client offset matches server file size, upload should proceed successfully."""
        # No exception should be raised
        await tus_upload_part(request_with_matching_offset)

    async def test_new_file_upload_with_zero_offset(
        self,
        request_with_zero_offset: MagicMock,
    ) -> None:
        """When both client offset and file size are 0, upload should proceed successfully."""
        # No exception should be raised
        await tus_upload_part(request_with_zero_offset)
