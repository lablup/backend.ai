"""
Tests for ScopeAdapter.
Tests the adapter layer for converting request DTOs to BatchQuerier objects.
"""

from __future__ import annotations

import pytest

from ai.backend.common.data.permission.types import GLOBAL_SCOPE_ID, ScopeType
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.rbac.request import (
    ScopeFilter,
    ScopeOrder,
    SearchScopesRequest,
)
from ai.backend.common.dto.manager.rbac.response import ScopeDTO
from ai.backend.common.dto.manager.rbac.types import OrderDirection, ScopeOrderField
from ai.backend.manager.api.rbac.scope_adapter import ScopeAdapter
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.types import ScopeData
from ai.backend.manager.repositories.base import OffsetPagination


class TestScopeAdapterBuildQuerier:
    """Tests for ScopeAdapter.build_querier method."""

    @pytest.fixture
    def adapter(self) -> ScopeAdapter:
        """Create ScopeAdapter instance."""
        return ScopeAdapter()

    def test_build_querier_domain_no_filter(self, adapter: ScopeAdapter) -> None:
        """Test building querier for domain scope without filters."""
        limit = 10
        offset = 0
        request = SearchScopesRequest(
            filter=None,
            order=None,
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.DOMAIN, request)

        assert querier.conditions == []
        assert querier.orders == []
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == limit
        assert querier.pagination.offset == offset

    def test_build_querier_domain_with_name_contains(self, adapter: ScopeAdapter) -> None:
        """Test building querier for domain scope with name contains filter."""
        limit = 10
        offset = 0
        request = SearchScopesRequest(
            filter=ScopeFilter(
                name=StringFilter(
                    i_contains="test",
                )
            ),
            order=None,
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.DOMAIN, request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_domain_with_name_equals(self, adapter: ScopeAdapter) -> None:
        """Test building querier for domain scope with name equals filter."""
        limit = 10
        offset = 0
        request = SearchScopesRequest(
            filter=ScopeFilter(
                name=StringFilter(
                    equals="exact-domain",
                )
            ),
            order=None,
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.DOMAIN, request)

        assert len(querier.conditions) == 1
        assert callable(querier.conditions[0])

    def test_build_querier_domain_with_name_starts_with(self, adapter: ScopeAdapter) -> None:
        """Test building querier for domain scope with name starts_with filter."""
        limit = 10
        offset = 0
        request = SearchScopesRequest(
            filter=ScopeFilter(
                name=StringFilter(
                    starts_with="prod-",
                )
            ),
            order=None,
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.DOMAIN, request)

        assert len(querier.conditions) == 1

    def test_build_querier_domain_with_name_ends_with(self, adapter: ScopeAdapter) -> None:
        """Test building querier for domain scope with name ends_with filter."""
        limit = 10
        offset = 0
        request = SearchScopesRequest(
            filter=ScopeFilter(
                name=StringFilter(
                    i_ends_with="-domain",
                )
            ),
            order=None,
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.DOMAIN, request)

        assert len(querier.conditions) == 1

    def test_build_querier_domain_with_ordering_name_asc(self, adapter: ScopeAdapter) -> None:
        """Test building querier for domain scope with name ascending order."""
        limit = 10
        offset = 0
        request = SearchScopesRequest(
            filter=None,
            order=[
                ScopeOrder(
                    field=ScopeOrderField.NAME,
                    direction=OrderDirection.ASC,
                )
            ],
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.DOMAIN, request)

        assert len(querier.orders) == 1

    def test_build_querier_domain_with_ordering_created_at_desc(
        self, adapter: ScopeAdapter
    ) -> None:
        """Test building querier for domain scope with created_at descending order."""
        limit = 10
        offset = 0
        request = SearchScopesRequest(
            filter=None,
            order=[
                ScopeOrder(
                    field=ScopeOrderField.CREATED_AT,
                    direction=OrderDirection.DESC,
                )
            ],
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.DOMAIN, request)

        assert len(querier.orders) == 1

    def test_build_querier_project_scope(self, adapter: ScopeAdapter) -> None:
        """Test building querier for project scope."""
        limit = 20
        offset = 10
        request = SearchScopesRequest(
            filter=ScopeFilter(
                name=StringFilter(
                    i_contains="project",
                )
            ),
            order=[
                ScopeOrder(
                    field=ScopeOrderField.NAME,
                    direction=OrderDirection.ASC,
                )
            ],
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.PROJECT, request)

        assert len(querier.conditions) == 1
        assert len(querier.orders) == 1
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == limit
        assert querier.pagination.offset == offset

    def test_build_querier_user_scope(self, adapter: ScopeAdapter) -> None:
        """Test building querier for user scope."""
        limit = 10
        offset = 0
        request = SearchScopesRequest(
            filter=ScopeFilter(
                name=StringFilter(
                    i_contains="admin",
                )
            ),
            order=None,
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.USER, request)

        assert len(querier.conditions) == 1

    def test_build_querier_global_scope(self, adapter: ScopeAdapter) -> None:
        """Test building querier for global scope returns empty querier."""
        limit = 10
        offset = 0
        request = SearchScopesRequest(
            filter=ScopeFilter(
                name=StringFilter(
                    i_contains="anything",
                )
            ),
            order=[
                ScopeOrder(
                    field=ScopeOrderField.NAME,
                    direction=OrderDirection.ASC,
                )
            ],
            limit=limit,
            offset=offset,
        )

        querier = adapter.build_querier(ScopeType.GLOBAL, request)

        # Global scope ignores filters and orders
        assert querier.conditions == []
        assert querier.orders == []


class TestScopeAdapterConvertToDTO:
    """Tests for ScopeAdapter.convert_to_dto method."""

    @pytest.fixture
    def adapter(self) -> ScopeAdapter:
        """Create ScopeAdapter instance."""
        return ScopeAdapter()

    def test_convert_to_dto_domain_scope(self, adapter: ScopeAdapter) -> None:
        """Test converting domain scope data to DTO."""
        domain_name = "test-domain"
        scope_data = ScopeData(
            id=ScopeId(scope_type=ScopeType.DOMAIN, scope_id=domain_name),
            name=domain_name,
        )

        dto = adapter.convert_to_dto(scope_data)

        assert isinstance(dto, ScopeDTO)
        assert dto.scope_type == ScopeType.DOMAIN
        assert dto.scope_id == domain_name
        assert dto.name == domain_name

    def test_convert_to_dto_project_scope(self, adapter: ScopeAdapter) -> None:
        """Test converting project scope data to DTO."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        project_name = "my-project"
        scope_data = ScopeData(
            id=ScopeId(scope_type=ScopeType.PROJECT, scope_id=project_id),
            name=project_name,
        )

        dto = adapter.convert_to_dto(scope_data)

        assert dto.scope_type == ScopeType.PROJECT
        assert dto.scope_id == project_id
        assert dto.name == project_name

    def test_convert_to_dto_user_scope(self, adapter: ScopeAdapter) -> None:
        """Test converting user scope data to DTO."""
        user_id = "660e8400-e29b-41d4-a716-446655440001"
        username = "john_doe"
        scope_data = ScopeData(
            id=ScopeId(scope_type=ScopeType.USER, scope_id=user_id),
            name=username,
        )

        dto = adapter.convert_to_dto(scope_data)

        assert dto.scope_type == ScopeType.USER
        assert dto.scope_id == user_id
        assert dto.name == username

    def test_convert_to_dto_global_scope(self, adapter: ScopeAdapter) -> None:
        """Test converting global scope data to DTO."""
        scope_data = ScopeData(
            id=ScopeId(scope_type=ScopeType.GLOBAL, scope_id=GLOBAL_SCOPE_ID),
            name=GLOBAL_SCOPE_ID,
        )

        dto = adapter.convert_to_dto(scope_data)

        assert dto.scope_type == ScopeType.GLOBAL
        assert dto.scope_id == GLOBAL_SCOPE_ID
        assert dto.name == GLOBAL_SCOPE_ID
