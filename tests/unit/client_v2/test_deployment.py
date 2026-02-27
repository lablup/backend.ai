"""Unit tests for DeploymentClient (SDK v2)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.deployment import DeploymentClient
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    RouteTrafficStatus,
)
from ai.backend.common.dto.manager.deployment import (
    ActivateRevisionResponse,
    CreateDeploymentResponse,
    CreateRevisionResponse,
    DeactivateRevisionResponse,
    DestroyDeploymentResponse,
    GetDeploymentResponse,
    GetRevisionResponse,
    ListDeploymentsResponse,
    ListRevisionsResponse,
    ListRoutesResponse,
    SearchDeploymentsRequest,
    SearchRevisionsRequest,
    SearchRoutesRequest,
    UpdateDeploymentRequest,
    UpdateDeploymentResponse,
    UpdateRouteTrafficStatusResponse,
)
from ai.backend.common.dto.manager.deployment.request import (
    ClusterConfigInput,
    CreateDeploymentRequest,
    CreateRevisionRequest,
    DeploymentMetadataInput,
    DeploymentStrategyInput,
    ImageInput,
    ModelMountConfigInput,
    ModelRuntimeConfigInput,
    NetworkAccessInput,
    ResourceConfigInput,
    RevisionInput,
    UpdateRouteTrafficStatusRequest,
)
from ai.backend.common.types import ClusterMode

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


def _make_deployment_client(mock_session: MagicMock) -> DeploymentClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return DeploymentClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    """Return (method, url, json_body) from the last ``session.request()`` call."""
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------

_SAMPLE_DEPLOYMENT_ID = uuid4()
_SAMPLE_REVISION_ID = uuid4()
_SAMPLE_ROUTE_ID = uuid4()
_SAMPLE_PROJECT_ID = uuid4()
_SAMPLE_USER_ID = uuid4()
_SAMPLE_IMAGE_ID = uuid4()
_SAMPLE_VFOLDER_ID = uuid4()

_SAMPLE_DEPLOYMENT_DTO = {
    "id": str(_SAMPLE_DEPLOYMENT_ID),
    "name": "my-deployment",
    "status": "READY",
    "tags": ["test"],
    "project_id": str(_SAMPLE_PROJECT_ID),
    "domain_name": "default",
    "created_at": "2025-01-01T00:00:00",
    "updated_at": "2025-01-01T00:00:00",
    "created_user_id": str(_SAMPLE_USER_ID),
    "network_config": {
        "open_to_public": False,
    },
    "replica_state": {
        "desired_replica_count": 1,
        "replica_ids": [],
    },
    "default_deployment_strategy": "ROLLING",
}

_SAMPLE_REVISION_DTO = {
    "id": str(_SAMPLE_REVISION_ID),
    "name": "rev-1",
    "cluster_config": {"mode": "single-node", "size": 1},
    "resource_config": {"resource_group_name": "default", "resource_slot": {"cpu": "1"}},
    "model_runtime_config": {"runtime_variant": "custom"},
    "model_mount_config": {
        "vfolder_id": str(_SAMPLE_VFOLDER_ID),
        "mount_destination": "/models",
        "definition_path": "model.py",
    },
    "created_at": "2025-01-01T00:00:00",
    "image_id": str(_SAMPLE_IMAGE_ID),
}

_SAMPLE_ROUTE_DTO: dict[str, Any] = {
    "id": str(_SAMPLE_ROUTE_ID),
    "endpoint_id": str(_SAMPLE_DEPLOYMENT_ID),
    "session_id": None,
    "status": "healthy",
    "traffic_ratio": 1.0,
    "created_at": "2025-01-01T00:00:00",
    "revision_id": str(_SAMPLE_REVISION_ID),
    "traffic_status": "active",
    "error_data": {},
}


# ---------------------------------------------------------------------------
# Deployment CRUD
# ---------------------------------------------------------------------------


class TestDeploymentCRUD:
    @pytest.mark.asyncio
    async def test_create_deployment(self) -> None:
        resp = _json_response({"deployment": _SAMPLE_DEPLOYMENT_DTO})
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=_SAMPLE_PROJECT_ID,
                domain_name="default",
                name="my-deployment",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            desired_replica_count=1,
            initial_revision=RevisionInput(
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_group="default",
                    resource_slots={"cpu": "1"},
                ),
                image=ImageInput(id=_SAMPLE_IMAGE_ID),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=_SAMPLE_VFOLDER_ID,
                    definition_path="model.py",
                ),
            ),
        )

        result = await dc.create_deployment(request)

        assert isinstance(result, CreateDeploymentResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/deployments")
        assert body is not None
        assert body["metadata"]["name"] == "my-deployment"

    @pytest.mark.asyncio
    async def test_search_deployments(self) -> None:
        resp = _json_response({
            "deployments": [_SAMPLE_DEPLOYMENT_DTO],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.search_deployments(SearchDeploymentsRequest())

        assert isinstance(result, ListDeploymentsResponse)
        assert len(result.deployments) == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/deployments/search")
        assert body is not None

    @pytest.mark.asyncio
    async def test_get_deployment(self) -> None:
        resp = _json_response({"deployment": _SAMPLE_DEPLOYMENT_DTO})
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.get_deployment(_SAMPLE_DEPLOYMENT_ID)

        assert isinstance(result, GetDeploymentResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert str(_SAMPLE_DEPLOYMENT_ID) in url

    @pytest.mark.asyncio
    async def test_update_deployment(self) -> None:
        resp = _json_response({"deployment": _SAMPLE_DEPLOYMENT_DTO})
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.update_deployment(
            _SAMPLE_DEPLOYMENT_ID,
            UpdateDeploymentRequest(name="updated-name"),
        )

        assert isinstance(result, UpdateDeploymentResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert str(_SAMPLE_DEPLOYMENT_ID) in url
        assert body is not None
        assert body["name"] == "updated-name"

    @pytest.mark.asyncio
    async def test_destroy_deployment(self) -> None:
        resp = _json_response({"deleted": True})
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.destroy_deployment(_SAMPLE_DEPLOYMENT_ID)

        assert isinstance(result, DestroyDeploymentResponse)
        assert result.deleted is True
        method, url, _ = _last_request_call(mock_session)
        assert method == "DELETE"
        assert str(_SAMPLE_DEPLOYMENT_ID) in url


# ---------------------------------------------------------------------------
# Revision operations
# ---------------------------------------------------------------------------


class TestRevisionOperations:
    @pytest.mark.asyncio
    async def test_create_revision(self) -> None:
        resp = _json_response({"revision": _SAMPLE_REVISION_DTO})
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        request = CreateRevisionRequest(
            cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
            resource_config=ResourceConfigInput(
                resource_group="default",
                resource_slots={"cpu": "1"},
            ),
            image=ImageInput(id=_SAMPLE_IMAGE_ID),
            model_runtime_config=ModelRuntimeConfigInput(),
            model_mount_config=ModelMountConfigInput(
                vfolder_id=_SAMPLE_VFOLDER_ID,
                definition_path="model.py",
            ),
        )

        result = await dc.create_revision(_SAMPLE_DEPLOYMENT_ID, request)

        assert isinstance(result, CreateRevisionResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert f"/deployments/{_SAMPLE_DEPLOYMENT_ID}/revisions" in url
        assert body is not None

    @pytest.mark.asyncio
    async def test_search_revisions(self) -> None:
        resp = _json_response({
            "revisions": [_SAMPLE_REVISION_DTO],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.search_revisions(_SAMPLE_DEPLOYMENT_ID, SearchRevisionsRequest())

        assert isinstance(result, ListRevisionsResponse)
        assert len(result.revisions) == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert f"/deployments/{_SAMPLE_DEPLOYMENT_ID}/revisions/search" in url
        assert body is not None

    @pytest.mark.asyncio
    async def test_get_revision(self) -> None:
        resp = _json_response({"revision": _SAMPLE_REVISION_DTO})
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.get_revision(_SAMPLE_DEPLOYMENT_ID, _SAMPLE_REVISION_ID)

        assert isinstance(result, GetRevisionResponse)
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert f"/deployments/{_SAMPLE_DEPLOYMENT_ID}/revisions/{_SAMPLE_REVISION_ID}" in url

    @pytest.mark.asyncio
    async def test_activate_revision(self) -> None:
        resp = _json_response({"success": True})
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.activate_revision(_SAMPLE_DEPLOYMENT_ID, _SAMPLE_REVISION_ID)

        assert isinstance(result, ActivateRevisionResponse)
        assert result.success is True
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert (
            f"/deployments/{_SAMPLE_DEPLOYMENT_ID}/revisions/{_SAMPLE_REVISION_ID}/activate" in url
        )

    @pytest.mark.asyncio
    async def test_deactivate_revision(self) -> None:
        resp = _json_response({"success": True})
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.deactivate_revision(_SAMPLE_DEPLOYMENT_ID, _SAMPLE_REVISION_ID)

        assert isinstance(result, DeactivateRevisionResponse)
        assert result.success is True
        method, url, _ = _last_request_call(mock_session)
        assert method == "POST"
        assert (
            f"/deployments/{_SAMPLE_DEPLOYMENT_ID}/revisions/{_SAMPLE_REVISION_ID}/deactivate"
            in url
        )


# ---------------------------------------------------------------------------
# Route operations
# ---------------------------------------------------------------------------


class TestRouteOperations:
    @pytest.mark.asyncio
    async def test_search_routes(self) -> None:
        resp = _json_response({
            "routes": [_SAMPLE_ROUTE_DTO],
            "pagination": {"total_count": 1, "has_next_page": False, "has_previous_page": False},
        })
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.search_routes(_SAMPLE_DEPLOYMENT_ID, SearchRoutesRequest())

        assert isinstance(result, ListRoutesResponse)
        assert len(result.routes) == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert f"/deployments/{_SAMPLE_DEPLOYMENT_ID}/routes/search" in url
        assert body is not None

    @pytest.mark.asyncio
    async def test_update_route_traffic_status(self) -> None:
        resp = _json_response({"route": _SAMPLE_ROUTE_DTO})
        mock_session = _make_request_session(resp)
        dc = _make_deployment_client(mock_session)

        result = await dc.update_route_traffic_status(
            _SAMPLE_DEPLOYMENT_ID,
            _SAMPLE_ROUTE_ID,
            UpdateRouteTrafficStatusRequest(traffic_status=RouteTrafficStatus.ACTIVE),
        )

        assert isinstance(result, UpdateRouteTrafficStatusResponse)
        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert (
            f"/deployments/{_SAMPLE_DEPLOYMENT_ID}/routes/{_SAMPLE_ROUTE_ID}/traffic-status" in url
        )
        assert body is not None
        assert body["traffic_status"] == "active"
