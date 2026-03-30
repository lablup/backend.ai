from __future__ import annotations

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.artifact_registry.request import (
    OffsetPaginationInput,
    PaginationInput,
    ScanArtifactsRequest,
    SearchArtifactsRequest,
)
from ai.backend.common.dto.manager.artifact_registry.response import (
    SearchArtifactsResponse,
)

from .conftest import RegistryFixtureData

EXTERNAL_SERVICE_XFAIL_REASON = (
    "Artifact registry scan operations require external service connectivity "
    "(HuggingFace API / Reservoir endpoint) which is not available in "
    "component test environment."
)


class TestSearchArtifacts:
    """Test the POST /artifact-registries/search endpoint with DB-seeded data."""

    async def test_search_returns_seeded_artifacts(
        self,
        admin_registry: BackendAIClientRegistry,
        registry_fixture: RegistryFixtureData,
    ) -> None:
        """Seeded HuggingFace and Reservoir artifacts are returned by search."""
        result = await admin_registry.artifact_registry.search_artifacts(
            SearchArtifactsRequest(
                pagination=PaginationInput(
                    offset=OffsetPaginationInput(offset=0, limit=100),
                ),
            ),
        )
        assert isinstance(result, SearchArtifactsResponse)
        artifact_ids = {a.id for a in result.artifacts}
        assert registry_fixture.hf_artifact_id in artifact_ids
        assert registry_fixture.reservoir_artifact_id in artifact_ids

    async def test_search_with_offset_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
        registry_fixture: RegistryFixtureData,
    ) -> None:
        """Offset pagination returns the correct subset."""
        result = await admin_registry.artifact_registry.search_artifacts(
            SearchArtifactsRequest(
                pagination=PaginationInput(
                    offset=OffsetPaginationInput(offset=0, limit=1),
                ),
            ),
        )
        assert isinstance(result, SearchArtifactsResponse)
        assert len(result.artifacts) == 1

    async def test_search_empty_result(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search with no seeded data returns empty list."""
        result = await admin_registry.artifact_registry.search_artifacts(
            SearchArtifactsRequest(
                pagination=PaginationInput(
                    offset=OffsetPaginationInput(offset=0, limit=100),
                ),
            ),
        )
        assert isinstance(result, SearchArtifactsResponse)
        assert len(result.artifacts) == 0


class TestScanArtifacts:
    @pytest.mark.xfail(strict=True, reason=EXTERNAL_SERVICE_XFAIL_REASON)
    async def test_scan_huggingface_artifacts(
        self,
        admin_registry: BackendAIClientRegistry,
        registry_fixture: RegistryFixtureData,
    ) -> None:
        """Scanning HuggingFace requires external API connectivity."""
        await admin_registry.artifact_registry.scan_artifacts(
            ScanArtifactsRequest(
                registry_id=registry_fixture.huggingface_registry_id,
                limit=5,
                order="downloads",
            ),
        )
