"""Component tests for VFolder project-scoped search via v2 REST API."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput
from ai.backend.common.types import VFolderUsageMode

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData
    from tests.component.vfolder.conftest import VFolderFactory

from ai.backend.manager.api.adapters.vfolder import VFolderAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.vfolder.handler import V2VFolderHandler
from ai.backend.manager.api.rest.v2.vfolder.registry import register_v2_vfolder_routes
from ai.backend.manager.data.vfolder.types import VFolderOwnershipType
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    vfolder_processors: VFolderProcessors,
) -> list[RouteRegistry]:
    """Register v2 vfolder REST routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.vfolder = vfolder_processors

    adapter = VFolderAdapter(processors)

    handler = V2VFolderHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_vfolder_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with superadmin keypair."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


class TestVFolderProjectSearch:
    """Tests for POST /v2/vfolders/projects/{project_id}/search."""

    async def test_returns_group_vfolders_in_project(
        self,
        admin_v2_registry: V2ClientRegistry,
        vfolder_factory: VFolderFactory,
        group_fixture: uuid.UUID,
    ) -> None:
        """Project search returns vfolders belonging to the project."""
        vf: dict[str, Any] = await vfolder_factory(
            ownership_type=VFolderOwnershipType.GROUP,
            group=str(group_fixture),
            usage_mode=VFolderUsageMode.GENERAL,
        )
        result = await admin_v2_registry.vfolder.project_search(
            group_fixture,
            SearchVFoldersInput(limit=20, offset=0),
        )
        found_ids = [item.id for item in result.items]
        assert vf["id"] in found_ids

    async def test_excludes_user_owned_vfolders(
        self,
        admin_v2_registry: V2ClientRegistry,
        vfolder_factory: VFolderFactory,
        group_fixture: uuid.UUID,
    ) -> None:
        """Project search excludes user-owned vfolders (only returns project-scoped ones)."""
        # Create a user-owned vfolder (not group-owned)
        await vfolder_factory(
            ownership_type=VFolderOwnershipType.USER,
        )
        result = await admin_v2_registry.vfolder.project_search(
            group_fixture,
            SearchVFoldersInput(limit=20, offset=0),
        )
        assert result.total_count == 0
        assert result.items == []

    async def test_empty_project_returns_empty_result(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """Project search on an empty project returns zero items."""
        result = await admin_v2_registry.vfolder.project_search(
            group_fixture,
            SearchVFoldersInput(limit=20, offset=0),
        )
        assert result.total_count == 0
        assert result.items == []
        assert result.has_next_page is False
        assert result.has_previous_page is False
