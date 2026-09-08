from __future__ import annotations

import uuid

import pytest

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.manager.models.idle_checker.scopes import IdleCheckerAssignmentOperationScope
from ai.backend.manager.models.idle_checker.searchers import IdleCheckerAssignmentSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    ScopedSearchIdleCheckerAssignmentsAction,
)


class TestScopedSearchIdleCheckerAssignmentsAction:
    @pytest.fixture
    def domain_id(self) -> DomainID:
        return DomainID(uuid.uuid4())

    @pytest.fixture
    def project_id(self) -> ProjectID:
        return ProjectID(uuid.uuid4())

    @pytest.fixture
    def action(
        self, domain_id: DomainID, project_id: ProjectID
    ) -> ScopedSearchIdleCheckerAssignmentsAction:
        return ScopedSearchIdleCheckerAssignmentsAction(
            scopes=[domain_id, project_id],
            searcher=IdleCheckerAssignmentSearcher(pagination=NoPagination()),
        )

    def test_scope_targets_name_each_scope_by_its_own_type(
        self,
        action: ScopedSearchIdleCheckerAssignmentsAction,
        domain_id: DomainID,
        project_id: ProjectID,
    ) -> None:
        assert action.scope_targets() == [
            ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=domain_id),
            ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=project_id),
        ]

    def test_operation_scopes_restrict_the_read_to_the_same_scopes(
        self,
        action: ScopedSearchIdleCheckerAssignmentsAction,
        domain_id: DomainID,
        project_id: ProjectID,
    ) -> None:
        assert action.operation_scopes() == [
            IdleCheckerAssignmentOperationScope(scope=domain_id),
            IdleCheckerAssignmentOperationScope(scope=project_id),
        ]
