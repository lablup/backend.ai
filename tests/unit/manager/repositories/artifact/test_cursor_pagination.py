"""Cursor and offset pagination of the artifact adapter's three searches."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.dto.manager.v2.artifact.request import (
    AdminSearchArtifactRevisionsInput,
    AdminSearchArtifactsGQLInput,
    AdminSearchArtifactsInput,
)
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.artifact.adapter import ArtifactAdapter
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactStatus,
    ArtifactType,
)
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.models.artifact_revision import ArtifactRevisionRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.artifact.actions.search import (
    SearchArtifactsAction,
    SearchArtifactsActionResult,
)
from ai.backend.manager.services.artifact.revision.actions.search import (
    SearchArtifactRevisionsAction,
    SearchArtifactRevisionsActionResult,
)
from ai.backend.testutils.db import with_tables

type _PageFetch = Callable[[str | None], Awaitable[tuple[list[uuid.UUID], bool]]]

_PAGE_SIZE = 2

_ROW_COUNT = 5


async def _walk(fetch: _PageFetch) -> list[uuid.UUID]:
    """Follow the last id of each page as the next cursor until no page is left."""
    visited: list[uuid.UUID] = []
    cursor: str | None = None
    while True:
        ids, has_more = await fetch(cursor)
        assert len(ids) <= _PAGE_SIZE
        visited.extend(ids)
        if not has_more:
            return visited
        cursor = encode_cursor(ids[-1])


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            DomainRow,
            ResourceGroupRow,
            UserResourcePolicyRow,
            ProjectResourcePolicyRow,
            KeyPairResourcePolicyRow,
            RoleRow,
            UserRoleRow,
            UserRow,
            KeyPairRow,
            ProjectRow,
            ContainerRegistryRow,
            ImageRow,
            VFolderRow,
            EndpointRow,
            DeploymentPolicyRow,
            DeploymentAutoScalingPolicyRow,
            RuntimeVariantRow,
            DeploymentRevisionPresetRow,
            DeploymentRevisionRow,
            SessionRow,
            AgentRow,
            KernelRow,
            ReplicaGroupRow,
            RoutingRow,
            ResourcePresetRow,
            ArtifactRow,
            ArtifactRevisionRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def artifact_ids(database: ExtendedAsyncSAEngine) -> list[uuid.UUID]:
    """Artifacts in forward order (id DESC)."""
    registry_id = uuid.uuid4()
    ids = [uuid.uuid4() for _ in range(_ROW_COUNT)]
    async with database.begin_session() as db_sess:
        for artifact_id in ids:
            db_sess.add(
                ArtifactRow(
                    id=artifact_id,
                    name="same-name",
                    type=ArtifactType.MODEL,
                    registry_id=registry_id,
                    registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    source_registry_id=registry_id,
                    source_registry_type=ArtifactRegistryType.HUGGINGFACE.value,
                    description="",
                    readonly=True,
                    availability=ArtifactAvailability.ALIVE.value,
                )
            )
    return sorted(ids, reverse=True)


@pytest.fixture
async def revision_ids(
    database: ExtendedAsyncSAEngine, artifact_ids: list[uuid.UUID]
) -> list[uuid.UUID]:
    """Revisions of one artifact in forward order (id DESC)."""
    ids = [uuid.uuid4() for _ in range(_ROW_COUNT)]
    async with database.begin_session() as db_sess:
        for index, revision_id in enumerate(ids):
            db_sess.add(
                ArtifactRevisionRow(
                    id=revision_id,
                    artifact_id=artifact_ids[0],
                    version=f"v{index}",
                    size=1024,
                    status=ArtifactStatus.AVAILABLE.value,
                )
            )
    return sorted(ids, reverse=True)


@pytest.fixture
def adapter(database: ExtendedAsyncSAEngine) -> ArtifactAdapter:
    repository = ArtifactRepository(db=database, v2_ops_provider=V2DBOpsProvider(database))

    async def search_artifacts(action: SearchArtifactsAction) -> SearchArtifactsActionResult:
        result = await repository.search_artifacts(searcher=action.searcher)
        return SearchArtifactsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_revisions(
        action: SearchArtifactRevisionsAction,
    ) -> SearchArtifactRevisionsActionResult:
        result = await repository.search_artifact_revisions(searcher=action.searcher)
        return SearchArtifactRevisionsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    processors = MagicMock()
    processors.search_artifacts.run = search_artifacts
    processors.revision.search_revision.run = search_revisions
    return ArtifactAdapter(processors)


class TestAdminSearchPagination:
    async def test_forward_pages_visit_every_row_once(
        self, adapter: ArtifactAdapter, artifact_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.admin_search(
                AdminSearchArtifactsInput(first=_PAGE_SIZE, after=cursor)
            )
            return [item.entity_id for item in payload.items], payload.has_next_page

        assert await _walk(fetch) == artifact_ids

    async def test_backward_pages_visit_every_row_once_in_reverse(
        self, adapter: ArtifactAdapter, artifact_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.admin_search(
                AdminSearchArtifactsInput(last=_PAGE_SIZE, before=cursor)
            )
            return [item.entity_id for item in payload.items], payload.has_previous_page

        assert await _walk(fetch) == list(reversed(artifact_ids))

    async def test_offset_page_follows_forward_order(
        self, adapter: ArtifactAdapter, artifact_ids: list[uuid.UUID]
    ) -> None:
        payload = await adapter.admin_search(AdminSearchArtifactsInput(limit=2, offset=2))

        assert [item.entity_id for item in payload.items] == artifact_ids[2:4]
        assert payload.total_count == len(artifact_ids)

    async def test_mixing_cursor_and_offset_is_rejected(self, adapter: ArtifactAdapter) -> None:
        with pytest.raises(InvalidGraphQLParameters):
            await adapter.admin_search(AdminSearchArtifactsInput(first=2, limit=2))


class TestGQLSearchPagination:
    async def test_forward_pages_visit_every_row_once(
        self, adapter: ArtifactAdapter, artifact_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.admin_search_gql(
                AdminSearchArtifactsGQLInput(first=_PAGE_SIZE, after=cursor)
            )
            return [item.entity_id for item in payload.items], payload.has_next_page

        assert await _walk(fetch) == artifact_ids

    async def test_backward_pages_visit_every_row_once_in_reverse(
        self, adapter: ArtifactAdapter, artifact_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.admin_search_gql(
                AdminSearchArtifactsGQLInput(last=_PAGE_SIZE, before=cursor)
            )
            return [item.entity_id for item in payload.items], payload.has_previous_page

        assert await _walk(fetch) == list(reversed(artifact_ids))

    async def test_offset_page_follows_forward_order(
        self, adapter: ArtifactAdapter, artifact_ids: list[uuid.UUID]
    ) -> None:
        payload = await adapter.admin_search_gql(AdminSearchArtifactsGQLInput(limit=2, offset=2))

        assert [item.entity_id for item in payload.items] == artifact_ids[2:4]
        assert payload.total_count == len(artifact_ids)

    async def test_mixing_cursor_and_offset_is_rejected(self, adapter: ArtifactAdapter) -> None:
        with pytest.raises(InvalidGraphQLParameters):
            await adapter.admin_search_gql(AdminSearchArtifactsGQLInput(last=2, offset=0))


class TestRevisionSearchPagination:
    async def test_forward_pages_visit_every_row_once(
        self, adapter: ArtifactAdapter, revision_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.search_revisions_gql(
                AdminSearchArtifactRevisionsInput(first=_PAGE_SIZE, after=cursor)
            )
            return [item.field_id for item in payload.items], payload.has_next_page

        assert await _walk(fetch) == revision_ids

    async def test_backward_pages_visit_every_row_once_in_reverse(
        self, adapter: ArtifactAdapter, revision_ids: list[uuid.UUID]
    ) -> None:
        async def fetch(cursor: str | None) -> tuple[list[uuid.UUID], bool]:
            payload = await adapter.search_revisions_gql(
                AdminSearchArtifactRevisionsInput(last=_PAGE_SIZE, before=cursor)
            )
            return [item.field_id for item in payload.items], payload.has_previous_page

        assert await _walk(fetch) == list(reversed(revision_ids))

    async def test_offset_page_follows_forward_order(
        self, adapter: ArtifactAdapter, revision_ids: list[uuid.UUID]
    ) -> None:
        payload = await adapter.search_revisions_gql(
            AdminSearchArtifactRevisionsInput(limit=2, offset=2)
        )

        assert [item.field_id for item in payload.items] == revision_ids[2:4]
        assert payload.total_count == len(revision_ids)

    async def test_mixing_cursor_and_offset_is_rejected(self, adapter: ArtifactAdapter) -> None:
        with pytest.raises(InvalidGraphQLParameters):
            await adapter.search_revisions_gql(AdminSearchArtifactRevisionsInput(first=2, offset=0))
