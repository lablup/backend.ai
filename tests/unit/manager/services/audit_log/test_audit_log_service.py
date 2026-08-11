"""
Tests for AuditLogService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.audit_log import AuditLogID
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData, AuditLogListResult
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.audit_log import (
    AuditLogRepository,
    EntityAuditLogOperationScope,
    TriggeredByAuditLogOperationScope,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
)
from ai.backend.manager.services.audit_log.actions.scoped_search import (
    EntityAuditLogTarget,
    ScopedSearchAuditLogsAction,
    TriggeredByAuditLogTarget,
)
from ai.backend.manager.services.audit_log.service import AuditLogService

_SAMPLE_ENTITY_ID = uuid.uuid4()


class TestAuditLogService:
    """Test cases for AuditLogService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked AuditLogRepository"""
        return MagicMock(spec=AuditLogRepository)

    @pytest.fixture
    def audit_log_service(self, mock_repository: MagicMock) -> AuditLogService:
        """Create AuditLogService instance with mocked repository"""
        return AuditLogService(audit_log_repository=mock_repository)

    @pytest.fixture
    def sample_audit_log_data(self) -> AuditLogData:
        """Create sample audit log data"""
        return AuditLogData(
            id=AuditLogID(uuid.uuid4()),
            action_id=uuid.uuid4(),
            entity_type="session",
            operation="create",
            action_name="create_session",
            created_at=datetime.now(UTC),
            description="Session created",
            status=OperationStatus.SUCCESS,
            action_kind=ActionKind.SINGLE_ENTITY,
            target_entity_id=str(_SAMPLE_ENTITY_ID),
            lookup_kind=None,
            lookup_key=None,
            request_id="req-456",
            triggered_by="user-789",
            acted_as=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            duration=timedelta(seconds=1),
        )

    # =========================================================================
    # Tests - Create
    # =========================================================================

    @pytest.fixture
    def scoped_search_user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def scoped_search_querier(self) -> BatchQuerier:
        return BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

    @pytest.fixture
    def scoped_search_targets(
        self, scoped_search_user_id: uuid.UUID
    ) -> list[SearchableActionTarget]:
        return [
            EntityAuditLogTarget(element_type=RBACElementType.VFOLDER, element_id="vf-1"),
            TriggeredByAuditLogTarget(user_id=scoped_search_user_id),
        ]

    @pytest.fixture
    def scoped_search_action(
        self,
        scoped_search_targets: list[SearchableActionTarget],
        scoped_search_querier: BatchQuerier,
    ) -> ScopedSearchAuditLogsAction:
        return ScopedSearchAuditLogsAction(
            items=scoped_search_targets, querier=scoped_search_querier
        )

    @pytest.fixture
    def mock_repository_with_one_scoped_hit(
        self,
        mock_repository: MagicMock,
        sample_audit_log_data: AuditLogData,
    ) -> MagicMock:
        mock_repository.scoped_search = AsyncMock(
            return_value=AuditLogListResult(
                items=[sample_audit_log_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        return mock_repository

    @pytest.fixture
    def mock_repository_with_empty_scoped_result(self, mock_repository: MagicMock) -> MagicMock:
        mock_repository.scoped_search = AsyncMock(
            return_value=AuditLogListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        return mock_repository

    # =========================================================================
    # Tests - Scoped Search
    # =========================================================================

    async def test_scoped_search_passes_per_target_search_scopes_to_repository(
        self,
        audit_log_service: AuditLogService,
        mock_repository_with_one_scoped_hit: MagicMock,
        scoped_search_action: ScopedSearchAuditLogsAction,
        scoped_search_querier: BatchQuerier,
        scoped_search_user_id: uuid.UUID,
        sample_audit_log_data: AuditLogData,
    ) -> None:
        """Service calls repository.scoped_search with one OperationScope per target."""
        result = await audit_log_service.scoped_search(scoped_search_action)

        assert result.data == [sample_audit_log_data]
        # Repository receives the same querier + the two target-derived SearchScopes.
        mock_repository_with_one_scoped_hit.scoped_search.assert_called_once()
        call_args = mock_repository_with_one_scoped_hit.scoped_search.call_args
        assert call_args.args[0] is scoped_search_querier
        scopes = list(call_args.args[1])
        assert scopes == [
            EntityAuditLogOperationScope(entity_type=RBACElementType.VFOLDER, entity_id="vf-1"),
            TriggeredByAuditLogOperationScope(triggered_by=str(scoped_search_user_id)),
        ]

    async def test_scoped_search_records_queried_rbac_refs_on_result(
        self,
        audit_log_service: AuditLogService,
        mock_repository_with_empty_scoped_result: MagicMock,
        scoped_search_action: ScopedSearchAuditLogsAction,
        scoped_search_user_id: uuid.UUID,
    ) -> None:
        """``element_refs()`` on the result returns the RBAC refs of the input targets."""
        result = await audit_log_service.scoped_search(scoped_search_action)

        assert result.element_refs() == [
            RBACElementRef(element_type=RBACElementType.VFOLDER, element_id="vf-1"),
            RBACElementRef(
                element_type=RBACElementType.USER, element_id=str(scoped_search_user_id)
            ),
        ]
