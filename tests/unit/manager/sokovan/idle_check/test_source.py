from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Final, override
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

import ai.backend.manager.sokovan.idle_check.preparer as idle_check_preparer
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.types import (
    BoundCheckerData,
    IdleCheckBatchData,
    IdleCheckerDefinitionData,
    IdleCheckTargetData,
)
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    IdleCheckContext,
    IdleChecker,
    IdleCheckerState,
    PrepareRequest,
)
from ai.backend.manager.sokovan.idle_check.preparer import IdleCheckPreparer
from ai.backend.manager.sokovan.idle_check.source import IdleCheckSource
from ai.backend.manager.sokovan.idle_check.types import IdleCheckCategory, IdleCheckTargetStatuses

_SPECS: Final[dict[CheckerType, IdleCheckerSpec]] = {
    CheckerType.SESSION_LIFETIME: IdleCheckerSpec(
        type=CheckerType.SESSION_LIFETIME, session_lifetime=SessionLifetimeSpec()
    ),
    CheckerType.NETWORK_TIMEOUT: IdleCheckerSpec(
        type=CheckerType.NETWORK_TIMEOUT, network=NetworkTimeoutSpec()
    ),
}


class PreparedState(IdleCheckerState):
    pass


class PrepareRecordingChecker(IdleChecker):
    """Records each prepare call as [(checker_id, session_ids), ...] per batch."""

    prepare_calls: list[list[tuple[IdleCheckerID, list[SessionId]]]]

    def __init__(self) -> None:
        self.prepare_calls = []

    @override
    async def prepare(
        self,
        context: IdleCheckContext,
        requests: Sequence[PrepareRequest],
    ) -> Mapping[IdleCheckerID, IdleCheckerState]:
        self.prepare_calls.append([
            (
                request.definition.checker_id,
                [session.session_id for session in request.sessions],
            )
            for request in requests
        ])
        return {request.definition.checker_id: PreparedState() for request in requests}

    @override
    def check_idle(self, session_id: SessionId, state: IdleCheckerState) -> bool:
        return False


def _bound_checker(checker_type: CheckerType) -> BoundCheckerData:
    return BoundCheckerData(
        scope=ScopeId(ScopeType.RESOURCE_GROUP, str(uuid4())),
        binding_created_at=datetime(2026, 1, 1, tzinfo=UTC),
        checker=IdleCheckerDefinitionData(
            checker_id=IdleCheckerID(uuid4()),
            checker_type=checker_type,
            target_session_types=frozenset({SessionTypes.INTERACTIVE}),
            spec=_SPECS[checker_type],
        ),
    )


def _target(session_id: SessionId, checkers: Sequence[BoundCheckerData]) -> IdleCheckTargetData:
    return IdleCheckTargetData(
        session=IdleCheckSession(
            session_id=session_id,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            starts_at=None,
        ),
        checkers=checkers,
    )


def _source(batch: IdleCheckBatchData) -> IdleCheckSource:
    repository = MagicMock()
    repository.fetch_idle_check_batch = AsyncMock(return_value=batch)
    return IdleCheckSource(repository, IdleCheckPreparer(IdleCheckContext()))


class TestIdleCheckSource:
    @pytest.fixture()
    def session_ids(self) -> tuple[SessionId, SessionId]:
        return (SessionId(uuid4()), SessionId(uuid4()))

    @pytest.fixture()
    def target_statuses(self) -> IdleCheckTargetStatuses:
        return IdleCheckTargetStatuses(session_statuses=frozenset([SessionStatus.RUNNING]))

    @pytest.fixture()
    def checker_registry(self, monkeypatch: pytest.MonkeyPatch) -> dict[CheckerType, IdleChecker]:
        """Swap the static checker_for dispatch with a test-local registry."""
        registry: dict[CheckerType, IdleChecker] = {}
        monkeypatch.setattr(idle_check_preparer, "checker_for", registry.get)
        return registry

    @pytest.fixture()
    def lifetime_checker(
        self, checker_registry: dict[CheckerType, IdleChecker]
    ) -> PrepareRecordingChecker:
        checker = PrepareRecordingChecker()
        checker_registry[CheckerType.SESSION_LIFETIME] = checker
        return checker

    @pytest.fixture()
    def network_checker(
        self, checker_registry: dict[CheckerType, IdleChecker]
    ) -> PrepareRecordingChecker:
        checker = PrepareRecordingChecker()
        checker_registry[CheckerType.NETWORK_TIMEOUT] = checker
        return checker

    @pytest.fixture()
    def lifetime_bound(self) -> BoundCheckerData:
        return _bound_checker(CheckerType.SESSION_LIFETIME)

    @pytest.fixture()
    def second_lifetime_bound(self) -> BoundCheckerData:
        return _bound_checker(CheckerType.SESSION_LIFETIME)

    @pytest.fixture()
    def network_bound(self) -> BoundCheckerData:
        return _bound_checker(CheckerType.NETWORK_TIMEOUT)

    @pytest.fixture()
    def source(
        self,
        session_ids: tuple[SessionId, SessionId],
        lifetime_bound: BoundCheckerData,
        second_lifetime_bound: BoundCheckerData,
        network_bound: BoundCheckerData,
    ) -> IdleCheckSource:
        """Two sessions sharing one definition; the second adds a same-type and another-type one."""
        first_session_id, second_session_id = session_ids
        batch = IdleCheckBatchData(
            targets=(
                _target(first_session_id, [lifetime_bound]),
                _target(second_session_id, [lifetime_bound, second_lifetime_bound, network_bound]),
            )
        )
        return _source(batch)

    async def test_prepares_each_checker_type_once_batching_its_definitions(
        self,
        source: IdleCheckSource,
        target_statuses: IdleCheckTargetStatuses,
        session_ids: tuple[SessionId, SessionId],
        lifetime_bound: BoundCheckerData,
        second_lifetime_bound: BoundCheckerData,
        network_bound: BoundCheckerData,
        lifetime_checker: PrepareRecordingChecker,
        network_checker: PrepareRecordingChecker,
    ) -> None:
        first_session_id, second_session_id = session_ids

        await source.fetch_reconcile_info(IdleCheckCategory.IDLE, target_statuses)

        assert lifetime_checker.prepare_calls == [
            [
                (lifetime_bound.checker.checker_id, [first_session_id, second_session_id]),
                (second_lifetime_bound.checker.checker_id, [second_session_id]),
            ],
        ]
        assert network_checker.prepare_calls == [
            [(network_bound.checker.checker_id, [second_session_id])],
        ]

    async def test_composes_prepared_targets_in_resolved_order(
        self,
        source: IdleCheckSource,
        target_statuses: IdleCheckTargetStatuses,
        session_ids: tuple[SessionId, SessionId],
        lifetime_checker: PrepareRecordingChecker,
        network_checker: PrepareRecordingChecker,
    ) -> None:
        first_session_id, second_session_id = session_ids

        reconcile_info = await source.fetch_reconcile_info(IdleCheckCategory.IDLE, target_statuses)

        assert [target.session_id for target in reconcile_info.targets] == [
            first_session_id,
            second_session_id,
        ]
        second_target = reconcile_info.targets[1]
        assert [prepared.checker for prepared in second_target.checkers] == [
            lifetime_checker,
            lifetime_checker,
            network_checker,
        ]
        # The same checker definition prepares once; its CheckerWithState is shared.
        assert reconcile_info.targets[0].checkers[0] is second_target.checkers[0]
