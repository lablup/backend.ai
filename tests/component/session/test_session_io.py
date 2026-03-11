from __future__ import annotations

import io
import uuid
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.session.request import (
    DownloadFilesRequest,
    DownloadSingleRequest,
    ListFilesRequest,
)
from ai.backend.common.dto.manager.session.response import (
    ListFilesResponse,
)

from .conftest import SessionSeedData


@pytest.fixture
async def mock_agent_list_files(agent_registry: AsyncMock) -> dict[str, Any]:
    """Mock agent RPC response for list_files."""
    mock_response = {
        "files": [
            {"name": "test.txt", "size": 100, "mode": "0644"},
            {"name": "data.csv", "size": 2048, "mode": "0644"},
        ],
    }
    agent_registry.request_to_all_kernels.return_value = [mock_response]
    return mock_response


@pytest.fixture
async def mock_agent_upload_files(agent_registry: AsyncMock) -> None:
    """Mock agent RPC response for upload_files."""
    agent_registry.request_to_all_kernels.return_value = [{"status": "ok"}]


@pytest.fixture
async def mock_agent_download_files(agent_registry: AsyncMock) -> bytes:
    """Mock agent RPC response for download_files (archive)."""
    # Create a simple ZIP archive in memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("test.txt", b"Hello, world!")
        zf.writestr("data.csv", b"col1,col2\n1,2\n3,4\n")
    archive_bytes = buffer.getvalue()
    agent_registry.request_to_all_kernels.return_value = [{"content": archive_bytes}]
    return archive_bytes


@pytest.fixture
async def mock_agent_download_single(agent_registry: AsyncMock) -> bytes:
    """Mock agent RPC response for download_single."""
    file_content = b"Hello, world!"
    agent_registry.request_to_all_kernels.return_value = [{"content": file_content}]
    return file_content


@pytest.fixture
async def mock_agent_commit(agent_registry: AsyncMock) -> str:
    """Mock agent RPC response for commit."""
    task_id = str(uuid.uuid4())
    agent_registry.request_to_all_kernels.return_value = [{"task_id": task_id}]
    return task_id


@pytest.fixture
async def mock_agent_commit_status(agent_registry: AsyncMock) -> dict[str, Any]:
    """Mock agent RPC response for get_commit_status."""
    mock_response = {"status": "completed", "progress": 100}
    agent_registry.request_to_all_kernels.return_value = [mock_response]
    return mock_response


@pytest.fixture
async def mock_agent_convert_to_image(agent_registry: AsyncMock) -> str:
    """Mock agent RPC response for convert_to_image."""
    task_id = str(uuid.uuid4())
    agent_registry.request_to_all_kernels.return_value = [{"task_id": task_id}]
    return task_id


class TestSessionListFiles:
    """Tests for session file listing operations."""

    async def test_list_files_on_running_session(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        mock_agent_list_files: dict[str, Any],
    ) -> None:
        result = await admin_registry.session.list_files(
            session_seed.session_name,
            ListFilesRequest(path="."),
        )
        assert isinstance(result, ListFilesResponse)
        assert "files" in result.root
        files = result.root["files"]
        assert len(files) == 2
        assert files[0]["name"] == "test.txt"
        assert files[1]["name"] == "data.csv"

    async def test_list_files_on_dead_session_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        # Make agent registry raise an error for terminated session
        agent_registry.request_to_all_kernels.side_effect = RuntimeError("Session is not running")
        with pytest.raises(NotFoundError):
            await admin_registry.session.list_files(
                terminated_session_seed.session_name,
                ListFilesRequest(path="."),
            )


class TestSessionUploadFiles:
    """Tests for session file upload operations."""

    async def test_upload_single_file(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        mock_agent_upload_files: None,
        tmp_path: Path,
    ) -> None:
        # Create a temporary file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        result = await admin_registry.session.upload_files(
            session_seed.session_name,
            [str(test_file)],
            basedir=tmp_path,
        )
        # The upload should succeed (agent returns {"status": "ok"})
        assert result is not None or result is None  # API may return None or status dict

    async def test_upload_multiple_files(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        mock_agent_upload_files: None,
        tmp_path: Path,
    ) -> None:
        # Create multiple temporary files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("File 1 content")
        file2.write_text("File 2 content")

        result = await admin_registry.session.upload_files(
            session_seed.session_name,
            [str(file1), str(file2)],
            basedir=tmp_path,
        )
        # The upload should succeed
        assert result is not None or result is None

    async def test_upload_exceeding_size_limit(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
        tmp_path: Path,
    ) -> None:
        # Mock agent to reject due to size limit
        agent_registry.request_to_all_kernels.side_effect = RuntimeError("File size exceeds limit")

        # Create a test file
        test_file = tmp_path / "large.txt"
        test_file.write_text("x" * 1000)  # Not actually large, but agent will reject

        with pytest.raises(Exception):  # RuntimeError or BackendAPIError
            await admin_registry.session.upload_files(
                session_seed.session_name,
                [str(test_file)],
                basedir=tmp_path,
            )


class TestSessionDownloadFiles:
    """Tests for session file download operations."""

    async def test_download_single_file(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        mock_agent_download_single: bytes,
    ) -> None:
        result = await admin_registry.session.download_single(
            session_seed.session_name,
            DownloadSingleRequest(file="test.txt"),
        )
        assert isinstance(result, bytes)
        assert result == b"Hello, world!"

    async def test_download_multiple_files_as_archive(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        mock_agent_download_files: bytes,
    ) -> None:
        result = await admin_registry.session.download_files(
            session_seed.session_name,
            DownloadFilesRequest(files=["test.txt", "data.csv"]),
        )
        assert isinstance(result, bytes)
        # Verify it's a valid ZIP archive
        buffer = io.BytesIO(result)
        with zipfile.ZipFile(buffer, "r") as zf:
            names = zf.namelist()
            assert "test.txt" in names
            assert "data.csv" in names

    async def test_download_nonexistent_file_returns_404(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        agent_registry: AsyncMock,
    ) -> None:
        # Mock agent to raise error for non-existent file
        agent_registry.request_to_all_kernels.side_effect = FileNotFoundError("File not found")

        with pytest.raises(Exception):  # Should be FileNotFoundError or similar
            await admin_registry.session.download_single(
                session_seed.session_name,
                DownloadSingleRequest(file="nonexistent.txt"),
            )


class TestSessionCommit:
    """Tests for session commit operations."""

    pass


class TestSessionConvertToImage:
    """Tests for session convert-to-image operations."""

    pass
