"""Client SDK functions for deployment system."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.deployment import (
    ActivateRevisionResponse,
    CreateDeploymentRequest,
    CreateDeploymentResponse,
    CreateRevisionRequest,
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
    UpdateRouteTrafficStatusRequest,
    UpdateRouteTrafficStatusResponse,
)

from ..request import Request
from .base import BaseFunction, api_function

__all__ = ("Deployment",)


class Deployment(BaseFunction):
    """
    Provides functions to interact with the deployment system.
    Supports deployments, revisions, and routes.
    """

    # Deployment CRUD operations

    @api_function
    @classmethod
    async def create(
        cls,
        request: CreateDeploymentRequest,
    ) -> CreateDeploymentResponse:
        """Create a new deployment."""
        rqst = Request("POST", "/deployments")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return CreateDeploymentResponse.model_validate(data)

    @api_function
    @classmethod
    async def search(
        cls,
        request: SearchDeploymentsRequest,
    ) -> ListDeploymentsResponse:
        """Search deployments with filters."""
        rqst = Request("POST", "/deployments/search")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListDeploymentsResponse.model_validate(data)

    @api_function
    @classmethod
    async def get(
        cls,
        deployment_id: UUID,
    ) -> GetDeploymentResponse:
        """Get a deployment by ID."""
        rqst = Request("GET", f"/deployments/{deployment_id}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return GetDeploymentResponse.model_validate(data)

    @api_function
    @classmethod
    async def update(
        cls,
        deployment_id: UUID,
        request: UpdateDeploymentRequest,
    ) -> UpdateDeploymentResponse:
        """Update a deployment."""
        rqst = Request("PATCH", f"/deployments/{deployment_id}")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return UpdateDeploymentResponse.model_validate(data)

    @api_function
    @classmethod
    async def destroy(
        cls,
        deployment_id: UUID,
    ) -> DestroyDeploymentResponse:
        """Destroy a deployment."""
        rqst = Request("DELETE", f"/deployments/{deployment_id}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return DestroyDeploymentResponse.model_validate(data)

    # Revision operations

    @api_function
    @classmethod
    async def create_revision(
        cls,
        deployment_id: UUID,
        request: CreateRevisionRequest,
    ) -> CreateRevisionResponse:
        """Create a new revision for a deployment."""
        rqst = Request("POST", f"/deployments/{deployment_id}/revisions")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return CreateRevisionResponse.model_validate(data)

    @api_function
    @classmethod
    async def search_revisions(
        cls,
        deployment_id: UUID,
        request: SearchRevisionsRequest,
    ) -> ListRevisionsResponse:
        """Search revisions for a deployment."""
        rqst = Request("POST", f"/deployments/{deployment_id}/revisions/search")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListRevisionsResponse.model_validate(data)

    @api_function
    @classmethod
    async def get_revision(
        cls,
        deployment_id: UUID,
        revision_id: UUID,
    ) -> GetRevisionResponse:
        """Get a revision by ID."""
        rqst = Request("GET", f"/deployments/{deployment_id}/revisions/{revision_id}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return GetRevisionResponse.model_validate(data)

    @api_function
    @classmethod
    async def activate_revision(
        cls,
        deployment_id: UUID,
        revision_id: UUID,
    ) -> ActivateRevisionResponse:
        """Activate a revision."""
        rqst = Request("POST", f"/deployments/{deployment_id}/revisions/{revision_id}/activate")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ActivateRevisionResponse.model_validate(data)

    @api_function
    @classmethod
    async def deactivate_revision(
        cls,
        deployment_id: UUID,
        revision_id: UUID,
    ) -> DeactivateRevisionResponse:
        """Deactivate a revision."""
        rqst = Request("POST", f"/deployments/{deployment_id}/revisions/{revision_id}/deactivate")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return DeactivateRevisionResponse.model_validate(data)

    # Route operations

    @api_function
    @classmethod
    async def search_routes(
        cls,
        deployment_id: UUID,
        request: SearchRoutesRequest,
    ) -> ListRoutesResponse:
        """Search routes for a deployment."""
        rqst = Request("POST", f"/deployments/{deployment_id}/routes/search")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return ListRoutesResponse.model_validate(data)

    @api_function
    @classmethod
    async def update_route_traffic_status(
        cls,
        deployment_id: UUID,
        route_id: UUID,
        request: UpdateRouteTrafficStatusRequest,
    ) -> UpdateRouteTrafficStatusResponse:
        """Update route traffic status."""
        rqst = Request("PATCH", f"/deployments/{deployment_id}/routes/{route_id}/traffic-status")
        rqst.set_json(request.model_dump(mode="json"))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return UpdateRouteTrafficStatusResponse.model_validate(data)
