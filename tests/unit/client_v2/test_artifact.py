"""Unit tests for ArtifactClient (SDK v2)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.artifact import ArtifactClient
from ai.backend.common.dto.manager.artifact import (
    ApproveRevisionResponse,
    CancelImportTaskRequest,
    CancelImportTaskResponse,
    CleanupRevisionsRequest,
    CleanupRevisionsResponse,
    GetRevisionDownloadProgressResponse,
    GetRevisionReadmeResponse,
    GetRevisionVerificationResultResponse,
    ImportArtifactsRequest,
    ImportArtifactsResponse,
    RejectRevisionResponse,
    UpdateArtifactRequest,
    UpdateArtifactResponse,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock aiohttp session whose ``request()`` returns *resp*."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _json_response(data: dict[str, Any], *, status: int = 200) -> AsyncMock:
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    return resp


def _make_artifact_client(mock_session: MagicMock) -> ArtifactClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return ArtifactClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    """Return (method, url, json_body) from the last ``session.request()`` call."""
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------

_SAMPLE_ARTIFACT_ID = uuid4()
_SAMPLE_ARTIFACT_REVISION_ID = uuid4()
_SAMPLE_REGISTRY_ID = uuid4()
_SAMPLE_SOURCE_REGISTRY_ID = uuid4()
_SAMPLE_VFOLDER_ID = uuid4()

_SAMPLE_ARTIFACT_REVISION_DTO: dict[str, Any] = {
    "id": str(_SAMPLE_ARTIFACT_REVISION_ID),
    "artifact_id": str(_SAMPLE_ARTIFACT_ID),
    "version": "1.0.0",
    "size": 1024,
    "status": "AVAILABLE",
    "remote_status": None,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
    "digest": "sha256:abc123",
    "verification_result": None,
}

_SAMPLE_ARTIFACT_DTO: dict[str, Any] = {
    "id": str(_SAMPLE_ARTIFACT_ID),
    "name": "test-model",
    "type": "MODEL",
    "description": "A test model",
    "registry_id": str(_SAMPLE_REGISTRY_ID),
    "source_registry_id": str(_SAMPLE_SOURCE_REGISTRY_ID),
    "registry_type": "huggingface",
    "source_registry_type": "huggingface",
    "availability": "ALIVE",
    "scanned_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
    "readonly": False,
    "extra": None,
}


# ---------------------------------------------------------------------------
# Artifact operations
# ---------------------------------------------------------------------------


class TestArtifactOperations:
    @pytest.mark.asyncio
    async def test_import_artifacts(self) -> None:
        resp = _json_response({
            "tasks": [
                {
                    "task_id": "task-123",
                    "artifact_revision": _SAMPLE_ARTIFACT_REVISION_DTO,
                }
            ],
        })
        mock_session = _make_request_session(resp)
        ac = _make_artifact_client(mock_session)

        result = await ac.import_artifacts(
            ImportArtifactsRequest(
                artifact_revision_ids=[_SAMPLE_ARTIFACT_REVISION_ID],
                vfolder_id=_SAMPLE_VFOLDER_ID,
            ),
        )

        assert isinstance(result, ImportArtifactsResponse)
        assert len(result.tasks) == 1
        assert result.tasks[0].task_id == "task-123"
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/artifacts/import")
        assert body is not None
        assert len(body["artifact_revision_ids"]) == 1

    @pytest.mark.asyncio
    async def test_update_artifact(self) -> None:
        resp = _json_response({"artifact": _SAMPLE_ARTIFACT_DTO})
        mock_session = _make_request_session(resp)
        ac = _make_artifact_client(mock_session)

        result = await ac.update_artifact(
            _SAMPLE_ARTIFACT_ID,
            UpdateArtifactRequest(readonly=True, description="Updated"),
        )

        assert isinstance(result, UpdateArtifactResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert str(_SAMPLE_ARTIFACT_ID) in url
        assert body is not None
        assert body["readonly"] is True
        assert body["description"] == "Updated"

    @pytest.mark.asyncio
    async def test_cancel_import_task(self) -> None:
        resp = _json_response({"artifact_revision": _SAMPLE_ARTIFACT_REVISION_DTO})
        mock_session = _make_request_session(resp)
        ac = _make_artifact_client(mock_session)

        result = await ac.cancel_import_task(
            CancelImportTaskRequest(artifact_revision_id=_SAMPLE_ARTIFACT_REVISION_ID),
        )

        assert isinstance(result, CancelImportTaskResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/artifacts/task/cancel")
        assert body is not None
        assert body["artifact_revision_id"] == _SAMPLE_ARTIFACT_REVISION_ID


# ---------------------------------------------------------------------------
# Revision operations
# ---------------------------------------------------------------------------


class TestRevisionOperations:
    @pytest.mark.asyncio
    async def test_cleanup_revisions(self) -> None:
        resp = _json_response({
            "artifact_revisions": [_SAMPLE_ARTIFACT_REVISION_DTO],
        })
        mock_session = _make_request_session(resp)
        ac = _make_artifact_client(mock_session)

        result = await ac.cleanup_revisions(
            CleanupRevisionsRequest(artifact_revision_ids=[_SAMPLE_ARTIFACT_REVISION_ID]),
        )

        assert isinstance(result, CleanupRevisionsResponse)
        assert len(result.artifact_revisions) == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/artifacts/revisions/cleanup")
        assert body is not None

    @pytest.mark.asyncio
    async def test_approve_revision(self) -> None:
        resp = _json_response({"artifact_revision": _SAMPLE_ARTIFACT_REVISION_DTO})
        mock_session = _make_request_session(resp)
        ac = _make_artifact_client(mock_session)

        result = await ac.approve_revision(_SAMPLE_ARTIFACT_REVISION_ID)

        assert isinstance(result, ApproveRevisionResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert f"/artifacts/revisions/{_SAMPLE_ARTIFACT_REVISION_ID}/approval" in url

    @pytest.mark.asyncio
    async def test_reject_revision(self) -> None:
        resp = _json_response({"artifact_revision": _SAMPLE_ARTIFACT_REVISION_DTO})
        mock_session = _make_request_session(resp)
        ac = _make_artifact_client(mock_session)

        result = await ac.reject_revision(_SAMPLE_ARTIFACT_REVISION_ID)

        assert isinstance(result, RejectRevisionResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert f"/artifacts/revisions/{_SAMPLE_ARTIFACT_REVISION_ID}/rejection" in url


# ---------------------------------------------------------------------------
# Revision queries
# ---------------------------------------------------------------------------


class TestRevisionQueries:
    @pytest.mark.asyncio
    async def test_get_revision_readme(self) -> None:
        resp = _json_response({"readme": "# My Model\nA great model."})
        mock_session = _make_request_session(resp)
        ac = _make_artifact_client(mock_session)

        result = await ac.get_revision_readme(_SAMPLE_ARTIFACT_REVISION_ID)

        assert isinstance(result, GetRevisionReadmeResponse)
        assert result.readme == "# My Model\nA great model."
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert f"/artifacts/revisions/{_SAMPLE_ARTIFACT_REVISION_ID}/readme" in url

    @pytest.mark.asyncio
    async def test_get_revision_verification_result(self) -> None:
        resp = _json_response({
            "verification_result": {
                "verifiers": {
                    "clamav": {
                        "success": True,
                        "infected_count": 0,
                        "scanned_at": "2025-01-01T00:00:00",
                        "scan_time": 1.5,
                        "scanned_count": 10,
                        "metadata": {},
                        "error": None,
                    }
                }
            }
        })
        mock_session = _make_request_session(resp)
        ac = _make_artifact_client(mock_session)

        result = await ac.get_revision_verification_result(_SAMPLE_ARTIFACT_REVISION_ID)

        assert isinstance(result, GetRevisionVerificationResultResponse)
        assert result.verification_result is not None
        assert "clamav" in result.verification_result.verifiers
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert f"/artifacts/revisions/{_SAMPLE_ARTIFACT_REVISION_ID}/verification-result" in url

    @pytest.mark.asyncio
    async def test_get_revision_download_progress(self) -> None:
        resp = _json_response({
            "download_progress": {
                "local": {
                    "progress": None,
                    "status": "AVAILABLE",
                },
                "remote": None,
            }
        })
        mock_session = _make_request_session(resp)
        ac = _make_artifact_client(mock_session)

        result = await ac.get_revision_download_progress(_SAMPLE_ARTIFACT_REVISION_ID)

        assert isinstance(result, GetRevisionDownloadProgressResponse)
        assert result.download_progress.local.status == "AVAILABLE"
        assert result.download_progress.remote is None
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert f"/artifacts/revisions/{_SAMPLE_ARTIFACT_REVISION_ID}/download-progress" in url
