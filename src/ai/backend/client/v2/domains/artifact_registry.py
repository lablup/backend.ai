from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.artifact_registry import (
    DelegateImportArtifactsRequest,
    DelegateImportArtifactsResponse,
    DelegateScanArtifactsRequest,
    DelegateScanArtifactsResponse,
    RetrieveArtifactModelResponse,
    ScanArtifactModelsRequest,
    ScanArtifactModelsResponse,
    ScanArtifactsRequest,
    ScanArtifactsResponse,
    SearchArtifactsRequest,
    SearchArtifactsResponse,
)


class ArtifactRegistryClient(BaseDomainClient):
    API_PREFIX = "/artifact-registries"

    # ---------------------------------------------------------------------------
    # Scan & Discovery
    # ---------------------------------------------------------------------------

    async def scan_artifacts(
        self,
        request: ScanArtifactsRequest,
    ) -> ScanArtifactsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/scan",
            request=request,
            response_model=ScanArtifactsResponse,
        )

    async def delegate_scan_artifacts(
        self,
        request: DelegateScanArtifactsRequest,
    ) -> DelegateScanArtifactsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/delegation/scan",
            request=request,
            response_model=DelegateScanArtifactsResponse,
        )

    async def delegate_import_artifacts(
        self,
        request: DelegateImportArtifactsRequest,
    ) -> DelegateImportArtifactsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/delegation/import",
            request=request,
            response_model=DelegateImportArtifactsResponse,
        )

    # ---------------------------------------------------------------------------
    # Search
    # ---------------------------------------------------------------------------

    async def search_artifacts(
        self,
        request: SearchArtifactsRequest,
    ) -> SearchArtifactsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/search",
            request=request,
            response_model=SearchArtifactsResponse,
        )

    # ---------------------------------------------------------------------------
    # Model scanning
    # ---------------------------------------------------------------------------

    async def scan_single_model(
        self,
        model_id: str,
        *,
        revision: str | None = None,
        registry_id: UUID | None = None,
    ) -> RetrieveArtifactModelResponse:
        params: dict[str, str] = {}
        if revision is not None:
            params["revision"] = revision
        if registry_id is not None:
            params["registry_id"] = str(registry_id)
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/model/{model_id}",
            response_model=RetrieveArtifactModelResponse,
            params=params,
        )

    async def scan_models_batch(
        self,
        request: ScanArtifactModelsRequest,
    ) -> ScanArtifactModelsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/models/batch",
            request=request,
            response_model=ScanArtifactModelsResponse,
        )
