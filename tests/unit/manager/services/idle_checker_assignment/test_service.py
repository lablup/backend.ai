from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerAssignmentSearchScope
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    IdleCheckerAssignmentScopeTarget,
    ScopedSearchIdleCheckerAssignmentsAction,
)
from ai.backend.manager.services.idle_checker_assignment.service import IdleCheckerAssignmentService


class TestIdleCheckerAssignmentService:
    @pytest.fixture
    def repository(self) -> AsyncMock:
        repository = AsyncMock()
        repository.scoped_search_assignments.return_value = SearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )
        return repository

    @pytest.fixture
    def service(self, repository: AsyncMock) -> IdleCheckerAssignmentService:
        return IdleCheckerAssignmentService(repository)

    @pytest.fixture
    def domain_target(self) -> IdleCheckerAssignmentScopeTarget:
        return IdleCheckerAssignmentScopeTarget(scope_type=ScopeType.DOMAIN, scope_id=uuid.uuid4())

    @pytest.fixture
    def project_target(self) -> IdleCheckerAssignmentScopeTarget:
        return IdleCheckerAssignmentScopeTarget(scope_type=ScopeType.PROJECT, scope_id=uuid.uuid4())

    @pytest.fixture
    def scoped_search_action(
        self,
        domain_target: IdleCheckerAssignmentScopeTarget,
        project_target: IdleCheckerAssignmentScopeTarget,
    ) -> ScopedSearchIdleCheckerAssignmentsAction:
        return ScopedSearchIdleCheckerAssignmentsAction(
            items=[domain_target, project_target],
            querier=BatchQuerier(pagination=NoPagination()),
        )

    async def test_scoped_search_converts_targets_to_scopes_and_refs(
        self,
        service: IdleCheckerAssignmentService,
        repository: AsyncMock,
        scoped_search_action: ScopedSearchIdleCheckerAssignmentsAction,
        domain_target: IdleCheckerAssignmentScopeTarget,
        project_target: IdleCheckerAssignmentScopeTarget,
    ) -> None:
        result = await service.scoped_search(scoped_search_action)

        called_scopes = repository.scoped_search_assignments.await_args.args[1]
        assert called_scopes == [
            IdleCheckerAssignmentSearchScope(
                scope_type=ScopeType.DOMAIN, scope_id=domain_target.scope_id
            ),
            IdleCheckerAssignmentSearchScope(
                scope_type=ScopeType.PROJECT, scope_id=project_target.scope_id
            ),
        ]
        assert result.queried_refs == [
            RBACElementRef(RBACElementType.DOMAIN, str(domain_target.scope_id)),
            RBACElementRef(RBACElementType.PROJECT, str(project_target.scope_id)),
        ]
