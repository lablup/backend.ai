"""
Unit tests for SchedulingHistoryService actions.
Tests the service layer with mocked repositories.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, create_autospec
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.data.entity.deployment import DEPLOYMENT_SCOPE_TYPE, DeploymentID
from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.replica_group_history import ReplicaGroupHistoryID
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE, SESSION_SCOPE_TYPE, SessionID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentHistoryData,
    DeploymentHistoryListResult,
    ReplicaGroupHandlerCategory,
    ReplicaGroupHistoryData,
    ReplicaGroupHistoryListResult,
    RouteHandlerCategory,
    RouteHistoryData,
    RouteHistoryListResult,
)
from ai.backend.manager.data.kernel.types import (
    KernelSchedulingHistoryData,
    KernelSchedulingHistoryListResult,
    KernelSchedulingPhase,
)
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SessionSchedulingHistoryListResult,
)
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.scheduling_history import SchedulingHistoryRepository
from ai.backend.manager.repositories.scheduling_history.types import (
    DeploymentHistoryOperationScope,
    DeploymentReplicaGroupHistoryOperationScope,
    RouteHistoryOperationScope,
    SessionKernelHistoryOperationScope,
    SessionSchedulingHistoryOperationScope,
)
from ai.backend.manager.services.scheduling_history.actions.global_search_replica_group_history import (
    GlobalSearchReplicaGroupHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.scoped_search_replica_group_history import (
    DeploymentReplicaGroupHistoryTarget,
    ScopedSearchReplicaGroupHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_deployment_history import (
    SearchDeploymentHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_deployment_scoped_history import (
    SearchDeploymentScopedHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_kernel_history import (
    SearchKernelHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_kernel_scoped_history import (
    SearchKernelScopedHistoryAction,
    SessionKernelHistoryTarget,
)
from ai.backend.manager.services.scheduling_history.actions.search_route_history import (
    SearchRouteHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_route_scoped_history import (
    SearchRouteScopedHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_session_history import (
    SearchSessionHistoryAction,
)
from ai.backend.manager.services.scheduling_history.actions.search_session_scoped_history import (
    SearchSessionScopedHistoryAction,
)
from ai.backend.manager.services.scheduling_history.service import SchedulingHistoryService

_NOW = datetime.now(tz=tzutc())
_SESSION_ID = SessionId(UUID("6ad4b5d1-3a4e-4a1f-9f6a-1c4a3f9d2b70"))
_DEPLOYMENT_ID = DeploymentID(UUID("2f1c9b8a-0d4e-4b2a-8c6f-7e3a1d5b90c4"))


@pytest.fixture
def mock_repository() -> MagicMock:
    mock: MagicMock = create_autospec(SchedulingHistoryRepository, instance=True)
    return mock


@pytest.fixture
def service(mock_repository: MagicMock) -> SchedulingHistoryService:
    return SchedulingHistoryService(repository=mock_repository)


@pytest.fixture
def querier() -> BatchQuerier:
    return BatchQuerier(pagination=NoPagination())


def _make_kernel_history() -> KernelSchedulingHistoryData:
    return KernelSchedulingHistoryData(
        id=KernelSchedulingHistoryID(uuid4()),
        kernel_id=KernelId(uuid4()),
        session_id=SessionId(uuid4()),
        phase="CREATING",
        from_status=KernelSchedulingPhase.PREPARED,
        to_status=KernelSchedulingPhase.CREATING,
        result=SchedulingResult.SUCCESS,
        error_code=None,
        message="",
        attempts=1,
        created_at=_NOW,
        updated_at=_NOW,
    )


@pytest.fixture
def replica_group_history() -> ReplicaGroupHistoryData:
    return ReplicaGroupHistoryData(
        id=ReplicaGroupHistoryID(uuid4()),
        replica_group_id=ReplicaGroupID(uuid4()),
        deployment_id=DeploymentID(uuid4()),
        category=ReplicaGroupHandlerCategory.LIFECYCLE,
        phase="DEPLOYING",
        from_status=None,
        to_status=None,
        result=SchedulingResult.SUCCESS,
        error_code=None,
        message="",
        sub_steps=[],
        attempts=1,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_session_history() -> SessionSchedulingHistoryData:
    return SessionSchedulingHistoryData(
        id=uuid4(),
        session_id=SessionId(uuid4()),
        phase="CREATING",
        from_status=None,
        to_status=None,
        result=SchedulingResult.SUCCESS,
        error_code=None,
        message="ok",
        sub_steps=[],
        attempts=1,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_deployment_history() -> DeploymentHistoryData:
    return DeploymentHistoryData(
        id=uuid4(),
        deployment_id=uuid4(),
        handler_category=DeploymentHandlerCategory.LIFECYCLE,
        phase="CREATING",
        from_status=None,
        to_status=None,
        result=SchedulingResult.SUCCESS,
        error_code=None,
        message="ok",
        sub_steps=[],
        attempts=1,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _make_route_history() -> RouteHistoryData:
    return RouteHistoryData(
        id=uuid4(),
        route_id=uuid4(),
        deployment_id=uuid4(),
        category=RouteHandlerCategory.LIFECYCLE,
        phase="CREATING",
        from_status=None,
        to_status=None,
        from_sub_status=None,
        to_sub_status=None,
        result=SchedulingResult.SUCCESS,
        error_code=None,
        message="ok",
        sub_steps=[],
        attempts=1,
        created_at=_NOW,
        updated_at=_NOW,
    )


class TestSearchSessionHistoryAction:
    async def test_returns_histories_with_pagination(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        history_item = _make_session_history()
        mock_repository.search_session_history.return_value = SessionSchedulingHistoryListResult(
            items=[history_item],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

        action = SearchSessionHistoryAction(querier=querier)
        result = await service.search_session_history(action)

        assert result.histories == [history_item]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_repository.search_session_history.assert_awaited_once_with(querier=querier)

    async def test_empty_result(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        mock_repository.search_session_history.return_value = SessionSchedulingHistoryListResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )

        action = SearchSessionHistoryAction(querier=querier)
        result = await service.search_session_history(action)

        assert result.histories == []
        assert result.total_count == 0


class TestSearchDeploymentHistoryAction:
    async def test_returns_deployment_histories(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        history_item = _make_deployment_history()
        mock_repository.search_deployment_history.return_value = DeploymentHistoryListResult(
            items=[history_item],
            total_count=1,
            has_next_page=True,
            has_previous_page=False,
        )

        action = SearchDeploymentHistoryAction(querier=querier)
        result = await service.search_deployment_history(action)

        assert result.histories == [history_item]
        assert result.total_count == 1
        assert result.has_next_page is True
        mock_repository.search_deployment_history.assert_awaited_once_with(querier=querier)


class TestSearchDeploymentScopedHistoryAction:
    async def test_scope_filters_by_deployment_id(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        deployment_id = uuid4()
        history_item = _make_deployment_history()
        mock_repository.search_deployment_scoped_history.return_value = DeploymentHistoryListResult(
            items=[history_item],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        scope = DeploymentHistoryOperationScope(deployment_id=deployment_id)

        action = SearchDeploymentScopedHistoryAction(
            deployment_id=DeploymentID(deployment_id), scope=scope, querier=querier
        )
        result = await service.search_deployment_scoped_history(action)

        assert result.histories == [history_item]
        mock_repository.search_deployment_scoped_history.assert_awaited_once_with(
            querier=querier, scope=scope
        )


class TestSearchSessionScopedHistoryAction:
    async def test_scope_filters_by_session_id(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        session_id = uuid4()
        history_item = _make_session_history()
        mock_repository.search_session_scoped_history.return_value = (
            SessionSchedulingHistoryListResult(
                items=[history_item],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        scope = SessionSchedulingHistoryOperationScope(session_id=session_id)

        action = SearchSessionScopedHistoryAction(
            session_id=SessionID(session_id), scope=scope, querier=querier
        )
        result = await service.search_session_scoped_history(action)

        assert result.histories == [history_item]
        mock_repository.search_session_scoped_history.assert_awaited_once_with(
            querier=querier, scope=scope
        )


class TestSearchRouteHistoryAction:
    async def test_returns_route_histories(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        history_item = _make_route_history()
        mock_repository.search_route_history.return_value = RouteHistoryListResult(
            items=[history_item],
            total_count=1,
            has_next_page=False,
            has_previous_page=True,
        )

        action = SearchRouteHistoryAction(querier=querier)
        result = await service.search_route_history(action)

        assert result.histories == [history_item]
        assert result.total_count == 1
        assert result.has_previous_page is True
        mock_repository.search_route_history.assert_awaited_once_with(querier=querier)


class TestSearchRouteScopedHistoryAction:
    async def test_scope_filters_by_route_id(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        route_id = ReplicaID(uuid4())
        history_item = _make_route_history()
        mock_repository.search_route_scoped_history.return_value = RouteHistoryListResult(
            items=[history_item],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )
        scope = RouteHistoryOperationScope(route_id=route_id)

        action = SearchRouteScopedHistoryAction(scope=scope, querier=querier)
        result = await service.search_route_scoped_history(action)

        assert result.histories == [history_item]
        mock_repository.search_route_scoped_history.assert_awaited_once_with(
            querier=querier, scope=scope
        )


class TestSearchKernelHistoryAction:
    async def test_returns_kernel_histories_with_pagination(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        history_item = _make_kernel_history()
        mock_repository.search_kernel_history.return_value = KernelSchedulingHistoryListResult(
            items=[history_item],
            total_count=1,
            has_next_page=True,
            has_previous_page=False,
        )

        action = SearchKernelHistoryAction(querier=querier)
        result = await service.search_kernel_history(action)

        assert result.items == [history_item]
        assert result.total_count == 1
        assert result.has_next_page is True
        assert result.has_previous_page is False
        mock_repository.search_kernel_history.assert_awaited_once_with(querier=querier)


class TestSearchKernelScopedHistoryAction:
    async def test_scopes_to_the_session_owning_the_kernels(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
    ) -> None:
        history_item = _make_kernel_history()
        mock_repository.search_kernel_scoped_history.return_value = (
            KernelSchedulingHistoryListResult(
                items=[history_item],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchKernelScopedHistoryAction(
            target=SessionKernelHistoryTarget(session_id=_SESSION_ID), querier=querier
        )
        result = await service.search_kernel_scoped_history(action)

        assert result.items == [history_item]
        # Authorized via session read: kernel permission records are intentionally
        # empty, so the session is the scope the search is bounded by.
        assert action.scope_targets() == (
            ScopeRef(scope_type=SESSION_SCOPE_TYPE, scope_id=_SESSION_ID),
        )
        assert action.entity_type() == SESSION_ENTITY_TYPE
        mock_repository.search_kernel_scoped_history.assert_awaited_once_with(
            querier=querier,
            scopes=[SessionKernelHistoryOperationScope(session_id=_SESSION_ID)],
        )


class TestGlobalSearchReplicaGroupHistoryAction:
    async def test_returns_histories(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
        replica_group_history: ReplicaGroupHistoryData,
    ) -> None:
        mock_repository.admin_search_replica_group_history.return_value = (
            ReplicaGroupHistoryListResult(
                items=[replica_group_history],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = GlobalSearchReplicaGroupHistoryAction(querier=querier)
        result = await service.global_search_replica_group_history(action)

        assert result.items == [replica_group_history]
        assert result.total_count == 1
        mock_repository.admin_search_replica_group_history.assert_awaited_once_with(querier=querier)


class TestScopedSearchReplicaGroupHistoryAction:
    async def test_scopes_to_the_owning_deployment(
        self,
        service: SchedulingHistoryService,
        mock_repository: MagicMock,
        querier: BatchQuerier,
        replica_group_history: ReplicaGroupHistoryData,
    ) -> None:
        mock_repository.scoped_search_replica_group_history.return_value = (
            ReplicaGroupHistoryListResult(
                items=[replica_group_history],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = ScopedSearchReplicaGroupHistoryAction(
            target=DeploymentReplicaGroupHistoryTarget(deployment_id=_DEPLOYMENT_ID),
            querier=querier,
        )
        result = await service.scoped_search_replica_group_history(action)

        assert result.items == [replica_group_history]
        # A replica group is no scope of its own, so the deployment bounds the search.
        assert action.scope_targets() == (
            ScopeRef(scope_type=DEPLOYMENT_SCOPE_TYPE, scope_id=_DEPLOYMENT_ID),
        )
        mock_repository.scoped_search_replica_group_history.assert_awaited_once_with(
            querier=querier,
            scopes=[DeploymentReplicaGroupHistoryOperationScope(deployment_id=_DEPLOYMENT_ID)],
        )
