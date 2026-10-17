"""A scoped audit-log read is recorded once per entity it names.

The bulk audit monitor writes one row per id ``entity_ids()`` answers, and the adapter
names every entity twice: once for what was done to it, once for what was done in it.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import pytest

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.audit_log.scopes import (
    AuditLogTarget,
    EntityAuditLogTarget,
    ScopeAuditLogTarget,
    TriggeredByAuditLogTarget,
)
from ai.backend.manager.models.audit_log.searchers import AuditLogSearcher
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.services.audit_log.actions.scoped_search import (
    ScopedSearchAuditLogsAction,
)


def _both_halves(owner: RuntimeEntityID) -> list[AuditLogTarget]:
    return [EntityAuditLogTarget(owner=owner), ScopeAuditLogTarget(owner=owner)]


def _action(targets: Sequence[AuditLogTarget]) -> ScopedSearchAuditLogsAction:
    return ScopedSearchAuditLogsAction(
        targets=targets,
        searcher=AuditLogSearcher(pagination=OffsetPagination(limit=10, offset=0)),
    )


class TestScopedSearchAuditLogsActionEntityIds:
    @pytest.fixture
    def first_session(self) -> RuntimeEntityID:
        return RuntimeEntityID(SessionEntityType(), uuid.uuid4())

    @pytest.fixture
    def second_session(self) -> RuntimeEntityID:
        return RuntimeEntityID(SessionEntityType(), uuid.uuid4())

    def test_one_entity_is_named_once(self, first_session: RuntimeEntityID) -> None:
        action = _action(_both_halves(first_session))

        assert list(action.entity_ids()) == [first_session]

    def test_two_entities_are_named_once_each_in_order(
        self, first_session: RuntimeEntityID, second_session: RuntimeEntityID
    ) -> None:
        action = _action([*_both_halves(first_session), *_both_halves(second_session)])

        assert list(action.entity_ids()) == [first_session, second_session]

    def test_triggered_user_is_named_beside_the_entity(
        self, first_session: RuntimeEntityID
    ) -> None:
        user_id = UserID(uuid.uuid4())
        action = _action([
            *_both_halves(first_session),
            TriggeredByAuditLogTarget(user_id=user_id),
        ])

        assert list(action.entity_ids()) == [first_session, user_id]

    def test_operation_scopes_keep_every_target(self, first_session: RuntimeEntityID) -> None:
        targets = _both_halves(first_session)
        action = _action(targets)

        assert list(action.operation_scopes()) == targets
