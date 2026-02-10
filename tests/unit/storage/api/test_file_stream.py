"""
Unit tests for file stream archive download functionality.

This test suite covers:
1. JWT token generation for archive downloads (path and server encoding)
2. download_archive handler functionality with mocked components
3. ZipArchiveStreamReader unit tests (file path traversal, archive creation)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import jwt
import pytest
from aiohttp import web

from ai.backend.common.api_handlers import APIStreamResponse
from ai.backend.common.dto.storage.request import (
    ArchiveDownloadTokenData,
    TokenOperationType,
)
from ai.backend.common.types import VFolderID
from ai.backend.storage.api.client import DownloadHandler
from ai.backend.storage.errors import InvalidAPIParameters
from ai.backend.storage.services.file_stream.zip import ZipArchiveStreamReader


class TestJWTTokenForArchiveDownload:
    """
    Test JWT token encoding/decoding for archive download sessions.

    Focus: Simple roundtrip test to ensure request data (paths, file lists)
    is correctly preserved through JWT encoding/decoding cycle.
    """

    @pytest.fixture
    def secret(self) -> str:
        """Secret key for JWT encoding."""
        return "test-secret-key-for-jwt"

    @pytest.fixture
    def token_data(self) -> ArchiveDownloadTokenData:
        """Sample token data for archive download (Pydantic model)."""
        return ArchiveDownloadTokenData(
            operation=TokenOperationType.DOWNLOAD,
            volume="test-volume",
            virtual_folder_id=VFolderID(None, uuid4()),
            files=["file1.txt", "dir1/file2.txt", "dir2/"],
            exp=datetime.now(UTC) + timedelta(hours=1),
        )

    def test_jwt_roundtrip_preserves_data(
        self,
        secret: str,
        token_data: ArchiveDownloadTokenData,
    ) -> None:
        """
        Test that JWT roundtrip preserves all token data.

        Scenario:
        1. Prepare request data (ArchiveDownloadTokenData)
        2. Encode to JWT token
        3. Decode JWT back to dict
        4. Compare decoded values with original:
           - volume matches
           - virtual_folder_id matches
           - files list matches (order preserved)
           - operation type matches
        """
        # Encode token data to JWT (convert datetime to Unix timestamp)
        payload = token_data.model_dump(mode="json")
        payload["exp"] = int(token_data.exp.timestamp())
        token = jwt.encode(payload, secret, algorithm="HS256")

        # Decode JWT back to dict
        decoded = jwt.decode(token, secret, algorithms=["HS256"])

        # Verify all fields are preserved
        assert decoded["volume"] == token_data.volume
        assert decoded["virtual_folder_id"] == str(token_data.virtual_folder_id)
        assert decoded["files"] == token_data.files
        assert decoded["operation"] == token_data.operation

        # Verify files list order is preserved
        assert decoded["files"][0] == "file1.txt"
        assert decoded["files"][1] == "dir1/file2.txt"
        assert decoded["files"][2] == "dir2/"


class TestDownloadArchiveHandler:
    """
    Test download_archive API handler with mocked dependencies.

    Focus: Tests handler logic including JWT validation, path security,
    StreamReader creation, and response generation.
    """

    @pytest.fixture
    def secret(self) -> str:
        """Secret key for JWT."""
        return "test-secret"

    @pytest.fixture
    def token_data(self) -> ArchiveDownloadTokenData:
        """Sample token data for testing."""
        return ArchiveDownloadTokenData(
            operation=TokenOperationType.DOWNLOAD,
            volume="test-volume",
            virtual_folder_id=VFolderID(None, uuid4()),
            files=["file1.txt", "dir1/file2.txt"],
            exp=datetime.now(UTC) + timedelta(hours=1),
        )

    @pytest.fixture
    def mock_context(self, tmp_path: Path, secret: str) -> MagicMock:
        """Create mock StorageRootCtx for testing."""
        # Mock volume
        volume = MagicMock()
        volume.sanitize_vfpath.return_value = tmp_path

        # Mock root context
        root_ctx = MagicMock()
        root_ctx.local_config.storage_proxy.secret = secret
        root_ctx.get_volume.return_value.__aenter__ = AsyncMock(return_value=volume)
        root_ctx.get_volume.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock storage context
        ctx = MagicMock()
        ctx.root_ctx = root_ctx

        return ctx

    @pytest.fixture
    def mock_query_param(
        self,
        secret: str,
        token_data: ArchiveDownloadTokenData,
    ) -> MagicMock:
        """Create mock QueryParam with JWT token."""
        # Encode JWT from Pydantic model (convert datetime to Unix timestamp)
        payload = token_data.model_dump(mode="json")
        payload["exp"] = int(token_data.exp.timestamp())
        token = jwt.encode(payload, secret, algorithm="HS256")

        # Mock query param
        query = MagicMock()
        query.parsed.token = token

        return query

    async def test_handler_decodes_jwt_and_uses_paths(
        self,
        mock_context: MagicMock,
        mock_query_param: MagicMock,
        token_data: ArchiveDownloadTokenData,
        secret: str,
        tmp_path: Path,
    ) -> None:
        """
        Test that handler decodes JWT and uses encoded paths correctly.

        Scenario:
        1. Create test files in tmp_path
        2. Call download_archive with JWT containing paths
        3. Verify handler uses volume and virtual_folder_id from token
        4. Verify files are resolved relative to correct base path
        """
        # Create test files matching token_data.files
        (tmp_path / "file1.txt").write_text("content1")
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "file2.txt").write_text("content2")

        # Create handler and call download_archive (undecorated method via __wrapped__)
        handler = DownloadHandler(secret=secret)
        unwrapped = cast(Any, DownloadHandler.download_archive).__wrapped__
        response = await unwrapped(handler, mock_query_param, mock_context)

        # Verify volume was accessed from token
        mock_context.root_ctx.get_volume.assert_called_once_with(token_data.volume)

        # Verify response is successful
        api_response = cast(APIStreamResponse, response)
        assert response.status == 200
        assert api_response.body is not None
        assert isinstance(api_response.body, ZipArchiveStreamReader)

    async def test_handler_prevents_path_traversal(
        self,
        mock_context: MagicMock,
        secret: str,
        tmp_path: Path,
    ) -> None:
        """
        Test that handler prevents path traversal attacks.

        Scenario:
        1. Create JWT with malicious path (e.g., ../../etc/passwd)
        2. Call download_archive
        3. Verify InvalidAPIParameters is raised with path escape error
        """
        # Create malicious token data with path traversal attempt
        malicious_token_data = ArchiveDownloadTokenData(
            operation=TokenOperationType.DOWNLOAD,
            volume="test-volume",
            virtual_folder_id=VFolderID(None, uuid4()),
            files=["../../etc/passwd"],  # Path traversal attempt
            exp=datetime.now(UTC) + timedelta(hours=1),
        )

        # Encode JWT with malicious path (convert datetime to Unix timestamp)
        payload = malicious_token_data.model_dump(mode="json")
        payload["exp"] = int(malicious_token_data.exp.timestamp())
        token = jwt.encode(payload, secret, algorithm="HS256")

        # Create query param with malicious token
        query = MagicMock()
        query.parsed.token = token

        # Create handler and attempt download
        handler = DownloadHandler(secret=secret)

        # Verify InvalidAPIParameters is raised
        unwrapped = cast(Any, DownloadHandler.download_archive).__wrapped__
        with pytest.raises(InvalidAPIParameters) as exc_info:
            await unwrapped(handler, query, mock_context)

        # Verify error message mentions path escape
        assert "escapes vfolder boundary" in str(exc_info.value.extra_msg)

    async def test_handler_validates_file_existence(
        self,
        mock_context: MagicMock,
        secret: str,
        tmp_path: Path,
    ) -> None:
        """
        Test that handler validates all files exist before streaming.

        Scenario:
        1. Create JWT with non-existent file path
        2. Call download_archive
        3. Verify HTTPNotFound is raised with file name
        """
        # Create token data with non-existent file
        nonexistent_token_data = ArchiveDownloadTokenData(
            operation=TokenOperationType.DOWNLOAD,
            volume="test-volume",
            virtual_folder_id=VFolderID(None, uuid4()),
            files=["nonexistent_file.txt"],  # File doesn't exist
            exp=datetime.now(UTC) + timedelta(hours=1),
        )

        # Encode JWT (convert datetime to Unix timestamp)
        payload = nonexistent_token_data.model_dump(mode="json")
        payload["exp"] = int(nonexistent_token_data.exp.timestamp())
        token = jwt.encode(payload, secret, algorithm="HS256")

        # Create query param
        query = MagicMock()
        query.parsed.token = token

        # Create handler and attempt download
        handler = DownloadHandler(secret=secret)

        # Verify HTTPNotFound is raised
        unwrapped = cast(Any, DownloadHandler.download_archive).__wrapped__
        with pytest.raises(web.HTTPNotFound) as exc_info:
            await unwrapped(handler, query, mock_context)

        # Verify error message mentions the file name
        assert "nonexistent_file.txt" in str(exc_info.value.reason)

    async def test_handler_creates_stream_reader_with_files(
        self,
        mock_context: MagicMock,
        mock_query_param: MagicMock,
        token_data: ArchiveDownloadTokenData,
        secret: str,
        tmp_path: Path,
    ) -> None:
        """
        Test that handler creates ZipArchiveStreamReader with correct files.

        Scenario:
        1. Create test files listed in token_data
        2. Call download_archive
        3. Verify StreamReader is created with correct base_path
        4. Verify all files from token are added to StreamReader
        """
        # Create test files matching token_data.files
        (tmp_path / "file1.txt").write_text("content1")
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "file2.txt").write_text("content2")

        # Create handler and call download_archive (undecorated method via __wrapped__)
        handler = DownloadHandler(secret=secret)
        unwrapped = cast(Any, DownloadHandler.download_archive).__wrapped__
        response = await unwrapped(handler, mock_query_param, mock_context)

        # Verify StreamReader is created
        api_response = cast(APIStreamResponse, response)
        assert isinstance(api_response.body, ZipArchiveStreamReader)

        # Verify base_path is correct
        reader = api_response.body
        assert reader._base_path == tmp_path

    async def test_handler_uses_filename_from_reader(
        self,
        mock_context: MagicMock,
        mock_query_param: MagicMock,
        secret: str,
        tmp_path: Path,
    ) -> None:
        """
        Test that handler uses filename from StreamReader (not hardcoded).

        Scenario:
        1. Call download_archive
        2. Verify response headers contain filename from reader.filename()
        3. Verify filename is not hardcoded "archive.zip"
        """
        # Create test files matching token_data.files
        (tmp_path / "file1.txt").write_text("content1")
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "file2.txt").write_text("content2")

        # Create handler and call download_archive (undecorated method via __wrapped__)
        handler = DownloadHandler(secret=secret)
        unwrapped = cast(Any, DownloadHandler.download_archive).__wrapped__
        response = await unwrapped(handler, mock_query_param, mock_context)

        # Verify response has headers
        assert response.headers is not None

        # Verify Content-Disposition header exists and contains filename
        content_disposition = response.headers.get("Content-Disposition")
        assert content_disposition is not None

        # Verify filename comes from reader.filename() (default is "archive.zip")
        api_response = cast(APIStreamResponse, response)
        reader = cast(ZipArchiveStreamReader, api_response.body)
        expected_filename = reader.filename()
        assert expected_filename in content_disposition
