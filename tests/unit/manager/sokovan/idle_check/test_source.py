from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import SessionId
from ai.backend.manager.data.idle_checker.types import IdleCheckSessionView, ScopeRef, ScopeType
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.types import IdleCheckSnapshot
from ai.backend.manager.sokovan.idle_check.source import IdleCheckSource
from ai.backend.manager.sokovan.idle_check.types import IdleCheckCategory, IdleCheckTargetStatuses


class TestIdleCheckSource:
    @pytest.fixture()
    def session_ids(self) -> tuple[SessionId, SessionId]:
        return (SessionId(uuid4()), SessionId(uuid4()))

    @pytest.fixture()
    def resource_group_scope(self) -> ScopeRef:
        return ScopeRef(ScopeType.RESOURCE_GROUP, uuid4())

    @pytest.fixture()
    def snapshot(
        self,
        session_ids: tuple[SessionId, SessionId],
        resource_group_scope: ScopeRef,
    ) -> IdleCheckSnapshot:
        first_session_id, second_session_id = session_ids
        return IdleCheckSnapshot(
            session_views_by_id={
                first_session_id: IdleCheckSessionView(
                    session_id=first_session_id,
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                    starts_at=datetime(2026, 1, 1, 1, tzinfo=UTC),
                    scopes=(resource_group_scope,),
                ),
                second_session_id: IdleCheckSessionView(
                    session_id=second_session_id,
                    created_at=datetime(2026, 1, 2, tzinfo=UTC),
                    starts_at=None,
                    scopes=(resource_group_scope,),
                ),
            },
            bindings_by_scope={},
            checkers_by_id={},
        )

    @pytest.fixture()
    def repository(self, snapshot: IdleCheckSnapshot) -> MagicMock:
        repository = MagicMock()
        repository.fetch_idle_check_snapshot = AsyncMock(return_value=snapshot)
        return repository

    @pytest.fixture()
    def source(self, repository: MagicMock) -> IdleCheckSource:
        return IdleCheckSource(repository)

    @pytest.fixture()
    def target_statuses(self) -> IdleCheckTargetStatuses:
        return IdleCheckTargetStatuses(session_statuses=frozenset([SessionStatus.RUNNING]))

    async def test_fetch_reconcile_info_uses_scope_snapshot(
        self,
        source: IdleCheckSource,
        repository: MagicMock,
        snapshot: IdleCheckSnapshot,
        session_ids: tuple[SessionId, SessionId],
        target_statuses: IdleCheckTargetStatuses,
    ) -> None:
        reconcile_info = await source.fetch_reconcile_info(IdleCheckCategory.IDLE, target_statuses)

        repository.fetch_idle_check_snapshot.assert_awaited_once_with(
            target_statuses.session_statuses
        )
        assert reconcile_info.snapshot is snapshot
        assert reconcile_info.entity_ids() == list(session_ids)
