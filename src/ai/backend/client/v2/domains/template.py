from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.template import (
    CreateClusterTemplateRequest,
    CreateClusterTemplateResponse,
    CreateSessionTemplateRequest,
    CreateSessionTemplateResponse,
    DeleteClusterTemplateRequest,
    DeleteClusterTemplateResponse,
    DeleteSessionTemplateRequest,
    DeleteSessionTemplateResponse,
    GetClusterTemplateRequest,
    GetClusterTemplateResponse,
    GetSessionTemplateRequest,
    GetSessionTemplateResponse,
    ListClusterTemplatesRequest,
    ListClusterTemplatesResponse,
    ListSessionTemplatesRequest,
    ListSessionTemplatesResponse,
    UpdateClusterTemplateRequest,
    UpdateClusterTemplateResponse,
    UpdateSessionTemplateRequest,
    UpdateSessionTemplateResponse,
)


class TemplateClient(BaseDomainClient):
    """Client for session and cluster template management endpoints."""

    # --- Session Template ---

    async def create_session_template(
        self,
        request: CreateSessionTemplateRequest,
    ) -> CreateSessionTemplateResponse:
        return await self._client.typed_request(
            "POST",
            "/template/session",
            request=request,
            response_model=CreateSessionTemplateResponse,
        )

    async def list_session_templates(
        self,
        request: ListSessionTemplatesRequest,
    ) -> ListSessionTemplatesResponse:
        params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            "/template/session",
            response_model=ListSessionTemplatesResponse,
            params=params,
        )

    async def get_session_template(
        self,
        template_id: str,
        request: GetSessionTemplateRequest | None = None,
    ) -> GetSessionTemplateResponse:
        params: dict[str, str] | None = None
        if request is not None:
            params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            f"/template/session/{template_id}",
            response_model=GetSessionTemplateResponse,
            params=params,
        )

    async def update_session_template(
        self,
        template_id: str,
        request: UpdateSessionTemplateRequest,
    ) -> UpdateSessionTemplateResponse:
        return await self._client.typed_request(
            "PUT",
            f"/template/session/{template_id}",
            request=request,
            response_model=UpdateSessionTemplateResponse,
        )

    async def delete_session_template(
        self,
        template_id: str,
        request: DeleteSessionTemplateRequest | None = None,
    ) -> DeleteSessionTemplateResponse:
        params: dict[str, str] | None = None
        if request is not None:
            params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "DELETE",
            f"/template/session/{template_id}",
            response_model=DeleteSessionTemplateResponse,
            params=params,
        )

    # --- Cluster Template ---

    async def create_cluster_template(
        self,
        request: CreateClusterTemplateRequest,
    ) -> CreateClusterTemplateResponse:
        return await self._client.typed_request(
            "POST",
            "/template/cluster",
            request=request,
            response_model=CreateClusterTemplateResponse,
        )

    async def list_cluster_templates(
        self,
        request: ListClusterTemplatesRequest,
    ) -> ListClusterTemplatesResponse:
        params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            "/template/cluster",
            response_model=ListClusterTemplatesResponse,
            params=params,
        )

    async def get_cluster_template(
        self,
        template_id: str,
        request: GetClusterTemplateRequest | None = None,
    ) -> GetClusterTemplateResponse:
        params: dict[str, str] | None = None
        if request is not None:
            params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            f"/template/cluster/{template_id}",
            response_model=GetClusterTemplateResponse,
            params=params,
        )

    async def update_cluster_template(
        self,
        template_id: str,
        request: UpdateClusterTemplateRequest,
    ) -> UpdateClusterTemplateResponse:
        return await self._client.typed_request(
            "PUT",
            f"/template/cluster/{template_id}",
            request=request,
            response_model=UpdateClusterTemplateResponse,
        )

    async def delete_cluster_template(
        self,
        template_id: str,
        request: DeleteClusterTemplateRequest | None = None,
    ) -> DeleteClusterTemplateResponse:
        params: dict[str, str] | None = None
        if request is not None:
            params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "DELETE",
            f"/template/cluster/{template_id}",
            response_model=DeleteClusterTemplateResponse,
            params=params,
        )
