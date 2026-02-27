from __future__ import annotations

import uuid

from ai.backend.client.v2.base_domain import BaseDomainClient
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


class DeploymentClient(BaseDomainClient):
    API_PREFIX = "/deployments"

    # ---------------------------------------------------------------------------
    # Deployment CRUD
    # ---------------------------------------------------------------------------

    async def create_deployment(
        self,
        request: CreateDeploymentRequest,
    ) -> CreateDeploymentResponse:
        return await self._client.typed_request(
            "POST",
            self.API_PREFIX,
            request=request,
            response_model=CreateDeploymentResponse,
        )

    async def search_deployments(
        self,
        request: SearchDeploymentsRequest,
    ) -> ListDeploymentsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/search",
            request=request,
            response_model=ListDeploymentsResponse,
        )

    async def get_deployment(
        self,
        deployment_id: uuid.UUID,
    ) -> GetDeploymentResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/{deployment_id}",
            response_model=GetDeploymentResponse,
        )

    async def update_deployment(
        self,
        deployment_id: uuid.UUID,
        request: UpdateDeploymentRequest,
    ) -> UpdateDeploymentResponse:
        return await self._client.typed_request(
            "PATCH",
            f"{self.API_PREFIX}/{deployment_id}",
            request=request,
            response_model=UpdateDeploymentResponse,
        )

    async def destroy_deployment(
        self,
        deployment_id: uuid.UUID,
    ) -> DestroyDeploymentResponse:
        return await self._client.typed_request(
            "DELETE",
            f"{self.API_PREFIX}/{deployment_id}",
            response_model=DestroyDeploymentResponse,
        )

    # ---------------------------------------------------------------------------
    # Revision operations
    # ---------------------------------------------------------------------------

    async def create_revision(
        self,
        deployment_id: uuid.UUID,
        request: CreateRevisionRequest,
    ) -> CreateRevisionResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{deployment_id}/revisions",
            request=request,
            response_model=CreateRevisionResponse,
        )

    async def search_revisions(
        self,
        deployment_id: uuid.UUID,
        request: SearchRevisionsRequest,
    ) -> ListRevisionsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{deployment_id}/revisions/search",
            request=request,
            response_model=ListRevisionsResponse,
        )

    async def get_revision(
        self,
        deployment_id: uuid.UUID,
        revision_id: uuid.UUID,
    ) -> GetRevisionResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/{deployment_id}/revisions/{revision_id}",
            response_model=GetRevisionResponse,
        )

    async def activate_revision(
        self,
        deployment_id: uuid.UUID,
        revision_id: uuid.UUID,
    ) -> ActivateRevisionResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{deployment_id}/revisions/{revision_id}/activate",
            response_model=ActivateRevisionResponse,
        )

    async def deactivate_revision(
        self,
        deployment_id: uuid.UUID,
        revision_id: uuid.UUID,
    ) -> DeactivateRevisionResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{deployment_id}/revisions/{revision_id}/deactivate",
            response_model=DeactivateRevisionResponse,
        )

    # ---------------------------------------------------------------------------
    # Route operations
    # ---------------------------------------------------------------------------

    async def search_routes(
        self,
        deployment_id: uuid.UUID,
        request: SearchRoutesRequest,
    ) -> ListRoutesResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{deployment_id}/routes/search",
            request=request,
            response_model=ListRoutesResponse,
        )

    async def update_route_traffic_status(
        self,
        deployment_id: uuid.UUID,
        route_id: uuid.UUID,
        request: UpdateRouteTrafficStatusRequest,
    ) -> UpdateRouteTrafficStatusResponse:
        return await self._client.typed_request(
            "PATCH",
            f"{self.API_PREFIX}/{deployment_id}/routes/{route_id}/traffic-status",
            request=request,
            response_model=UpdateRouteTrafficStatusResponse,
        )
