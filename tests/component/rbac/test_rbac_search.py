"""
Component tests for RBAC search operations.

Comprehensive search tests covering:
- Role search with various filters and pagination
- Scope search
- Entity search
- Permission boundary tests
"""

from __future__ import annotations

import secrets
from typing import Any

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.rbac.request import (
    RoleFilter,
    RoleOrder,
    SearchEntitiesRequest,
    SearchRolesRequest,
    SearchScopesRequest,
)
from ai.backend.common.dto.manager.rbac.response import (
    SearchEntitiesResponse,
    SearchRolesResponse,
    SearchScopesResponse,
)
from ai.backend.common.dto.manager.rbac.types import (
    OrderDirection,
    RoleOrderField,
    RoleSource,
    RoleStatus,
)

from .conftest import RoleFactory


class TestRoleSearch:
    """Test role search with filters, pagination, and sorting."""

    async def test_search_all_roles_no_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search all roles without filter returns paginated list."""
        # Create at least one test role
        await role_factory()

        result = await admin_registry.rbac.search_roles(SearchRolesRequest())

        assert isinstance(result, SearchRolesResponse)
        assert result.pagination.total >= 1
        assert len(result.roles) >= 1
        assert result.pagination.offset == 0

    async def test_search_with_status_filter_active(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with status filter ACTIVE returns only active roles."""
        unique = secrets.token_hex(4)
        active_role = await role_factory(
            name=f"active-{unique}",
            status=RoleStatus.ACTIVE,
        )

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=f"active-{unique}"),
                    statuses=[RoleStatus.ACTIVE],
                ),
            )
        )

        assert result.pagination.total >= 1
        assert all(r.status == RoleStatus.ACTIVE for r in result.roles)
        assert any(r.id == active_role.role.id for r in result.roles)

    async def test_search_with_status_filter_inactive(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with status filter INACTIVE returns only inactive roles."""
        unique = secrets.token_hex(4)
        inactive_role = await role_factory(
            name=f"inactive-{unique}",
            status=RoleStatus.INACTIVE,
        )

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=f"inactive-{unique}"),
                    statuses=[RoleStatus.INACTIVE],
                ),
            )
        )

        assert result.pagination.total >= 1
        assert all(r.status == RoleStatus.INACTIVE for r in result.roles)
        assert any(r.id == inactive_role.role.id for r in result.roles)

    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with name filter returns only matching roles."""
        unique = secrets.token_hex(4)
        marker = f"unique-search-{unique}"
        created = await role_factory(name=marker)

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=marker)),
            )
        )

        assert result.pagination.total >= 1
        assert all(marker in r.name for r in result.roles)
        assert any(r.id == created.role.id for r in result.roles)

    async def test_search_with_pagination_limit(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with pagination limit returns correct page size."""
        unique = secrets.token_hex(4)
        # Create 3 roles
        for i in range(3):
            await role_factory(name=f"page-{unique}-{i}")

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"page-{unique}")),
                limit=2,
                offset=0,
            )
        )

        assert isinstance(result, SearchRolesResponse)
        assert result.pagination.total == 3
        assert len(result.roles) == 2
        assert result.pagination.limit == 2
        assert result.pagination.offset == 0

    async def test_search_with_pagination_offset(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with pagination offset skips correct number of items."""
        unique = secrets.token_hex(4)
        # Create 3 roles
        for i in range(3):
            await role_factory(name=f"offset-{unique}-{i}")

        # Get first page
        page1 = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"offset-{unique}")),
                limit=2,
                offset=0,
            )
        )

        # Get second page
        page2 = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"offset-{unique}")),
                limit=2,
                offset=2,
            )
        )

        assert page1.pagination.total == 3
        assert len(page1.roles) == 2
        assert page2.pagination.total == 3
        assert len(page2.roles) == 1
        # Ensure different roles on different pages
        page1_ids = {r.id for r in page1.roles}
        page2_ids = {r.id for r in page2.roles}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_search_with_sorting_asc(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with sorting ascending returns correctly ordered results."""
        unique = secrets.token_hex(4)
        # Create roles with specific names for sorting
        await role_factory(name=f"sort-{unique}-z-last")
        await role_factory(name=f"sort-{unique}-a-first")
        await role_factory(name=f"sort-{unique}-m-middle")

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"sort-{unique}")),
                order=[RoleOrder(field=RoleOrderField.NAME, direction=OrderDirection.ASC)],
            )
        )

        assert len(result.roles) == 3
        names = [r.name for r in result.roles]
        assert names == sorted(names)
        assert names[0].endswith("a-first")
        assert names[2].endswith("z-last")

    async def test_search_with_sorting_desc(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with sorting descending returns correctly ordered results."""
        unique = secrets.token_hex(4)
        # Create roles with specific names for sorting
        await role_factory(name=f"desc-{unique}-a-first")
        await role_factory(name=f"desc-{unique}-z-last")
        await role_factory(name=f"desc-{unique}-m-middle")

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"desc-{unique}")),
                order=[RoleOrder(field=RoleOrderField.NAME, direction=OrderDirection.DESC)],
            )
        )

        assert len(result.roles) == 3
        names = [r.name for r in result.roles]
        assert names == sorted(names, reverse=True)
        assert names[0].endswith("z-last")
        assert names[2].endswith("a-first")

    async def test_search_empty_result(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search with non-matching filter returns empty result."""
        unique = secrets.token_hex(4)
        nonexistent_marker = f"this-role-definitely-does-not-exist-{unique}"

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=nonexistent_marker)),
            )
        )

        assert isinstance(result, SearchRolesResponse)
        assert result.pagination.total == 0
        assert len(result.roles) == 0

    async def test_search_with_source_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with source filter returns only roles from specified source."""
        unique = secrets.token_hex(4)
        custom_role = await role_factory(
            name=f"custom-{unique}",
            source=RoleSource.CUSTOM,
        )

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=f"custom-{unique}"),
                    sources=[RoleSource.CUSTOM],
                ),
            )
        )

        assert result.pagination.total >= 1
        assert all(r.source == RoleSource.CUSTOM for r in result.roles)
        assert any(r.id == custom_role.role.id for r in result.roles)


class TestScopeSearch:
    """Test scope search operations."""

    async def test_search_domain_scopes(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search domain scopes returns list of domains."""
        result = await admin_registry.rbac.search_scopes(
            "domain",
            SearchScopesRequest(),
        )

        assert isinstance(result, SearchScopesResponse)
        # Should have at least the default domain
        assert result.pagination.total >= 1
        assert len(result.items) >= 1

    async def test_search_scopes_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search scopes with pagination returns correct page."""
        result = await admin_registry.rbac.search_scopes(
            "domain",
            SearchScopesRequest(limit=1, offset=0),
        )

        assert isinstance(result, SearchScopesResponse)
        assert result.pagination.limit == 1
        assert len(result.items) <= 1


class TestEntitySearch:
    """Test entity search operations."""

    async def test_search_entities_in_domain(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: Any,
    ) -> None:
        """Search entities within a domain scope."""
        # Search for users in the test domain
        result = await admin_registry.rbac.search_entities(
            scope_type="domain",
            scope_id=domain_fixture,
            entity_type="user",
            request=SearchEntitiesRequest(),
        )

        assert isinstance(result, SearchEntitiesResponse)
        # Test domain may be empty, just verify search works
        assert result.pagination.total >= 0
        assert isinstance(result.items, list)

    async def test_search_entities_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: Any,
    ) -> None:
        """Search entities with pagination returns correct page."""
        result = await admin_registry.rbac.search_entities(
            scope_type="domain",
            scope_id=domain_fixture,
            entity_type="user",
            request=SearchEntitiesRequest(limit=1, offset=0),
        )

        assert isinstance(result, SearchEntitiesResponse)
        assert result.pagination.limit == 1
        assert len(result.items) <= 1


class TestSearchPermissionBoundaries:
    """Test search permission boundaries for regular users."""

    async def test_regular_user_cannot_search_roles(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user cannot search roles (admin-only operation)."""
        # All RBAC search operations are under /admin/rbac/ endpoints
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.search_roles(SearchRolesRequest())

    async def test_regular_user_cannot_search_scopes(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user cannot search scopes (admin-only operation)."""
        # Attempting to search scopes should be denied for regular users
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.search_scopes("domain", SearchScopesRequest())

    async def test_regular_user_cannot_search_entities(
        self,
        user_registry: BackendAIClientRegistry,
        domain_fixture: Any,
    ) -> None:
        """Regular user cannot search entities."""
        # Entity search should be admin-only
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.search_entities(
                scope_type="domain",
                scope_id=domain_fixture,
                entity_type="user",
                request=SearchEntitiesRequest(),
            )
