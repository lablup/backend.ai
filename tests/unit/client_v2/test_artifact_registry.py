"""Unit tests for ArtifactRegistryClient (SDK v2)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.artifact_registry import ArtifactRegistryClient
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.common.dto.manager.artifact_registry import (
    DelegateeTargetInput,
    DelegateImportArtifactsRequest,
    DelegateImportArtifactsResponse,
    DelegateScanArtifactsRequest,
    DelegateScanArtifactsResponse,
    ImportArtifactsOptionsInput,
    OffsetPaginationInput,
    PaginationInput,
    RetrieveArtifactModelResponse,
    ScanArtifactModelsRequest,
    ScanArtifactModelsResponse,
    ScanArtifactsRequest,
    ScanArtifactsResponse,
    SearchArtifactsRequest,
    SearchArtifactsResponse,
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


def _make_artifact_registry_client(mock_session: MagicMock) -> ArtifactRegistryClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return ArtifactRegistryClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    """Return (method, url, json_body) from the last ``session.request()`` call."""
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------

_SAMPLE_REGISTRY_ID = uuid4()
_SAMPLE_SOURCE_REGISTRY_ID = uuid4()
_SAMPLE_ARTIFACT_ID = uuid4()
_SAMPLE_REVISION_ID = uuid4()
_SAMPLE_DELEGATEE_RESERVOIR_ID = uuid4()
_SAMPLE_TARGET_REGISTRY_ID = uuid4()

_SAMPLE_REVISION_DTO = {
    "id": str(_SAMPLE_REVISION_ID),
    "artifact_id": str(_SAMPLE_ARTIFACT_ID),
    "version": "main",
    "size": 1024,
    "status": "SCANNED",
    "remote_status": None,
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
    "digest": "sha256:abc123",
    "verification_result": None,
}

_SAMPLE_ARTIFACT_DTO = {
    "id": str(_SAMPLE_ARTIFACT_ID),
    "name": "microsoft/DialoGPT-medium",
    "type": "MODEL",
    "description": "A conversational AI model",
    "registry_id": str(_SAMPLE_REGISTRY_ID),
    "source_registry_id": str(_SAMPLE_SOURCE_REGISTRY_ID),
    "registry_type": "huggingface",
    "source_registry_type": "huggingface",
    "availability": "ALIVE",
    "scanned_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
    "readonly": True,
    "extra": None,
    "revisions": [_SAMPLE_REVISION_DTO],
}

_SAMPLE_REVISION_DATA_DTO = {
    **_SAMPLE_REVISION_DTO,
    "readme": "# Model README",
}

_SAMPLE_ARTIFACT_WITH_REVISIONS_DTO = {
    **{k: v for k, v in _SAMPLE_ARTIFACT_DTO.items() if k != "revisions"},
    "revisions": [_SAMPLE_REVISION_DATA_DTO],
}


class TestScanOperations:
    @pytest.mark.asyncio
    async def test_scan_artifacts(self) -> None:
        resp = _json_response({"artifacts": [_SAMPLE_ARTIFACT_DTO]})
        mock_session = _make_request_session(resp)
        client = _make_artifact_registry_client(mock_session)

        request = ScanArtifactsRequest(
            registry_id=_SAMPLE_REGISTRY_ID,
            artifact_type="MODEL",
            limit=50,
            search="DialoGPT",
        )
        result = await client.scan_artifacts(request)

        assert isinstance(result, ScanArtifactsResponse)
        assert len(result.artifacts) == 1
        assert result.artifacts[0].name == "microsoft/DialoGPT-medium"
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/artifact-registries/scan")
        assert body is not None
        assert body["limit"] == 50
        assert body["search"] == "DialoGPT"

    @pytest.mark.asyncio
    async def test_delegate_scan_artifacts(self) -> None:
        resp = _json_response({
            "artifacts": [_SAMPLE_ARTIFACT_DTO],
            "source_registry_id": str(_SAMPLE_SOURCE_REGISTRY_ID),
            "source_registry_type": "reservoir",
            "readme_data": {},
        })
        mock_session = _make_request_session(resp)
        client = _make_artifact_registry_client(mock_session)

        request = DelegateScanArtifactsRequest(
            delegator_reservoir_id=_SAMPLE_REGISTRY_ID,
            delegatee_target=DelegateeTargetInput(
                delegatee_reservoir_id=_SAMPLE_DELEGATEE_RESERVOIR_ID,
                target_registry_id=_SAMPLE_TARGET_REGISTRY_ID,
            ),
            limit=10,
            search="gpt",
        )
        result = await client.delegate_scan_artifacts(request)

        assert isinstance(result, DelegateScanArtifactsResponse)
        assert len(result.artifacts) == 1
        assert result.source_registry_id == _SAMPLE_SOURCE_REGISTRY_ID
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/artifact-registries/delegation/scan")
        assert body is not None
        assert body["delegatee_target"]["delegatee_reservoir_id"] == str(_SAMPLE_DELEGATEE_RESERVOIR_ID)

    @pytest.mark.asyncio
    async def test_delegate_import_artifacts(self) -> None:
        resp = _json_response({
            "tasks": [
                {
                    "task_id": "task-001",
                    "artifact_revision": _SAMPLE_REVISION_DTO,
                }
            ]
        })
        mock_session = _make_request_session(resp)
        client = _make_artifact_registry_client(mock_session)

        request = DelegateImportArtifactsRequest(
            artifact_revision_ids=[_SAMPLE_REVISION_ID],
            delegator_reservoir_id=_SAMPLE_REGISTRY_ID,
            artifact_type="MODEL",
            options=ImportArtifactsOptionsInput(force=True),
        )
        result = await client.delegate_import_artifacts(request)

        assert isinstance(result, DelegateImportArtifactsResponse)
        assert len(result.tasks) == 1
        assert result.tasks[0].task_id == "task-001"
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/artifact-registries/delegation/import")
        assert body is not None
        assert body["artifact_revision_ids"] == [str(_SAMPLE_REVISION_ID)]
        assert body["options"]["force"] is True


class TestSearchOperations:
    @pytest.mark.asyncio
    async def test_search_artifacts(self) -> None:
        resp = _json_response({"artifacts": [_SAMPLE_ARTIFACT_DTO]})
        mock_session = _make_request_session(resp)
        client = _make_artifact_registry_client(mock_session)

        request = SearchArtifactsRequest(
            pagination=PaginationInput(
                offset=OffsetPaginationInput(offset=0, limit=50),
            ),
        )
        result = await client.search_artifacts(request)

        assert isinstance(result, SearchArtifactsResponse)
        assert len(result.artifacts) == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/artifact-registries/search")
        assert body is not None
        assert body["pagination"]["offset"]["limit"] == 50


class TestModelScanning:
    @pytest.mark.asyncio
    async def test_scan_single_model(self) -> None:
        resp = _json_response({"artifact": _SAMPLE_ARTIFACT_WITH_REVISIONS_DTO})
        mock_session = _make_request_session(resp)
        client = _make_artifact_registry_client(mock_session)

        result = await client.scan_single_model(
            "microsoft/DialoGPT-medium",
            revision="main",
            registry_id=_SAMPLE_REGISTRY_ID,
        )

        assert isinstance(result, RetrieveArtifactModelResponse)
        assert result.artifact.name == "microsoft/DialoGPT-medium"
        assert result.artifact.revisions[0].readme == "# Model README"
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert "/artifact-registries/model/microsoft/DialoGPT-medium" in url
        assert body is None

    @pytest.mark.asyncio
    async def test_scan_single_model_minimal(self) -> None:
        resp = _json_response({"artifact": _SAMPLE_ARTIFACT_WITH_REVISIONS_DTO})
        mock_session = _make_request_session(resp)
        client = _make_artifact_registry_client(mock_session)

        result = await client.scan_single_model("bert-base-uncased")

        assert isinstance(result, RetrieveArtifactModelResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert "/artifact-registries/model/bert-base-uncased" in url
        # No params when revision/registry_id not provided
        _, kwargs = mock_session.request.call_args
        assert kwargs.get("params") == {}

    @pytest.mark.asyncio
    async def test_scan_models_batch(self) -> None:
        resp = _json_response({"artifacts": [_SAMPLE_ARTIFACT_DTO]})
        mock_session = _make_request_session(resp)
        client = _make_artifact_registry_client(mock_session)

        request = ScanArtifactModelsRequest(
            models=[
                ModelTarget(model_id="microsoft/DialoGPT-medium", revision="main"),
                ModelTarget(model_id="bert-base-uncased"),
            ],
            registry_id=_SAMPLE_REGISTRY_ID,
        )
        result = await client.scan_models_batch(request)

        assert isinstance(result, ScanArtifactModelsResponse)
        assert len(result.artifacts) == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/artifact-registries/models/batch")
        assert body is not None
        assert len(body["models"]) == 2
        assert body["models"][0]["model_id"] == "microsoft/DialoGPT-medium"
