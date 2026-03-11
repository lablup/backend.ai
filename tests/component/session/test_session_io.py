from __future__ import annotations

import io
import uuid
import zipfile
from typing import Any
from unittest.mock import AsyncMock

import pytest


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

    pass


class TestSessionUploadFiles:
    """Tests for session file upload operations."""

    pass


class TestSessionDownloadFiles:
    """Tests for session file download operations."""

    pass


class TestSessionCommit:
    """Tests for session commit operations."""

    pass


class TestSessionConvertToImage:
    """Tests for session convert-to-image operations."""

    pass
