from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Protocol
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    IdleCheckPhase,
    NetworkTimeoutSpec,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleCheckerContext,
)
from ai.backend.manager.sokovan.idle_check.checkers.network_timeout import (
    NetworkTimeoutChecker,
)

_BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)
_BASE_TIMESTAMP = _BASE_TIME.timestamp()
_EXISTING_EXPIRE_AT = _BASE_TIME + timedelta(seconds=15)


class AssignmentFactory(Protocol):
    def __call__(
        self,
        *,
        max_network_inactivity_seconds: int,
        sessions: Sequence[IdleCheckSession],
    ) -> CheckerAssignment: ...


class TestNetworkTimeoutSpec:
    def test_rejects_zero_timeout(self) -> None:
        with pytest.raises(ValidationError):
            NetworkTimeoutSpec(max_network_inactivity_seconds=0)


class TestNetworkTimeoutChecker:
    @pytest.fixture()
    def valkey_live(self) -> AsyncMock:
        def count_active_connections(session_ids: Sequence[SessionId]) -> dict[SessionId, int]:
            return dict.fromkeys(session_ids, 0)

        client = AsyncMock(spec=ValkeyLiveClient)
        client.get_session_last_access_batch.side_effect = lambda session_ids: dict.fromkeys(
            session_ids, _BASE_TIMESTAMP
        )
        client.count_active_connections_batch.side_effect = count_active_connections
        return client

    @pytest.fixture()
    def checker(self, valkey_live: AsyncMock) -> NetworkTimeoutChecker:
        return NetworkTimeoutChecker(valkey_live)

    @pytest.fixture()
    def session(self) -> IdleCheckSession:
        return IdleCheckSession(
            session_id=SessionId(uuid4()),
            created_at=_BASE_TIME,
            starts_at=_BASE_TIME,
            expire_at=_EXISTING_EXPIRE_AT,
        )

    @pytest.fixture()
    def assignment_factory(self) -> AssignmentFactory:
        def create_assignment(
            *,
            max_network_inactivity_seconds: int,
            sessions: Sequence[IdleCheckSession],
        ) -> CheckerAssignment:
            return CheckerAssignment(
                definition=IdleCheckerDefinitionData(
                    checker_id=IdleCheckerID(uuid4()),
                    checker_type=CheckerType.NETWORK_TIMEOUT,
                    target_session_types=frozenset({SessionTypes.INTERACTIVE}),
                    spec=IdleCheckerSpec(
                        type=CheckerType.NETWORK_TIMEOUT,
                        network=NetworkTimeoutSpec(
                            max_network_inactivity_seconds=max_network_inactivity_seconds,
                        ),
                    ),
                ),
                sessions=sessions,
            )

        return create_assignment

    @pytest.fixture()
    def assignment(
        self,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
    ) -> CheckerAssignment:
        return assignment_factory(max_network_inactivity_seconds=30, sessions=(session,))

    @pytest.fixture()
    def active_connection_valkey(
        self,
        valkey_live: AsyncMock,
        session: IdleCheckSession,
    ) -> AsyncMock:
        valkey_live.count_active_connections_batch.side_effect = lambda _session_ids: {
            session.session_id: 1
        }
        return valkey_live

    @pytest.fixture()
    def active_request_valkey(
        self,
        valkey_live: AsyncMock,
    ) -> AsyncMock:
        valkey_live.get_session_last_access_batch.side_effect = lambda session_ids: dict.fromkeys(
            session_ids, 0.0
        )
        return valkey_live

    @pytest.fixture()
    def missing_last_access_valkey(
        self,
        valkey_live: AsyncMock,
    ) -> AsyncMock:
        valkey_live.get_session_last_access_batch.side_effect = lambda session_ids: dict.fromkeys(
            session_ids
        )
        return valkey_live

    @pytest.fixture()
    def missing_last_access_with_active_connection_valkey(
        self,
        missing_last_access_valkey: AsyncMock,
        session: IdleCheckSession,
    ) -> AsyncMock:
        missing_last_access_valkey.count_active_connections_batch.side_effect = (
            lambda _session_ids: {session.session_id: 1}
        )
        return missing_last_access_valkey

    @pytest.fixture()
    def definition_specific_assignments(
        self,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
    ) -> tuple[CheckerAssignment, CheckerAssignment]:
        return (
            assignment_factory(
                max_network_inactivity_seconds=10,
                sessions=(replace(session, expire_at=_BASE_TIME + timedelta(seconds=10)),),
            ),
            assignment_factory(
                max_network_inactivity_seconds=30,
                sessions=(replace(session, expire_at=_BASE_TIME + timedelta(seconds=30)),),
            ),
        )

    async def test_disconnected_session_before_expiration_is_idle(
        self,
        checker: NetworkTimeoutChecker,
        session: IdleCheckSession,
        assignment: CheckerAssignment,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=10)),
        )

        assert len(judgments) == 1
        assert judgments[0].session_id == session.session_id
        assert judgments[0].status is IdleCheckPhase.IDLE
        assert judgments[0].expire_at == _EXISTING_EXPIRE_AT
        assert judgments[0].message.startswith("No active network connection:")

    async def test_disconnected_session_without_expiration_starts_timeout(
        self,
        checker: NetworkTimeoutChecker,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
    ) -> None:
        assignment = assignment_factory(
            max_network_inactivity_seconds=30,
            sessions=(replace(session, expire_at=None),),
        )

        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=10)),
        )

        assert judgments[0].status is IdleCheckPhase.IDLE
        assert judgments[0].expire_at == _BASE_TIME + timedelta(seconds=40)

    async def test_disconnected_session_at_expiration_is_idle_expired(
        self,
        checker: NetworkTimeoutChecker,
        assignment: CheckerAssignment,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=20)),
        )

        assert judgments[0].status is IdleCheckPhase.IDLE_EXPIRED
        assert judgments[0].expire_at == _EXISTING_EXPIRE_AT
        assert judgments[0].message.startswith("Maximum network inactivity exceeded:")
        assert "last_access_at=2026-01-01 00:00:00 UTC" in judgments[0].message

    async def test_missing_last_access_before_expiration_is_idle(
        self,
        checker: NetworkTimeoutChecker,
        assignment: CheckerAssignment,
        missing_last_access_valkey: AsyncMock,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=10)),
        )

        assert judgments[0].status is IdleCheckPhase.IDLE
        assert judgments[0].expire_at == _EXISTING_EXPIRE_AT
        assert "last_access_at=None" in judgments[0].message

    async def test_missing_last_access_after_expiration_is_idle_expired(
        self,
        checker: NetworkTimeoutChecker,
        assignment: CheckerAssignment,
        missing_last_access_valkey: AsyncMock,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=20)),
        )

        assert judgments[0].status is IdleCheckPhase.IDLE_EXPIRED
        assert judgments[0].expire_at == _EXISTING_EXPIRE_AT
        assert "last_access_at=None" in judgments[0].message

    async def test_missing_last_access_with_active_connection_is_active(
        self,
        checker: NetworkTimeoutChecker,
        assignment: CheckerAssignment,
        missing_last_access_with_active_connection_valkey: AsyncMock,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=60)),
        )

        assert judgments[0].status is IdleCheckPhase.ACTIVE
        assert judgments[0].expire_at == _BASE_TIME + timedelta(seconds=90)

    async def test_active_connection_refreshes_expiration(
        self,
        checker: NetworkTimeoutChecker,
        assignment: CheckerAssignment,
        active_connection_valkey: AsyncMock,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(
                current_time=_BASE_TIME + timedelta(seconds=60),
            ),
        )

        assert judgments[0].status is IdleCheckPhase.ACTIVE
        assert judgments[0].expire_at == _BASE_TIME + timedelta(seconds=90)
        assert judgments[0].message.startswith("Network activity detected:")

    async def test_active_request_refreshes_expiration(
        self,
        checker: NetworkTimeoutChecker,
        assignment: CheckerAssignment,
        active_request_valkey: AsyncMock,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=60)),
        )

        assert judgments[0].status is IdleCheckPhase.ACTIVE
        assert judgments[0].expire_at == _BASE_TIME + timedelta(seconds=90)

    async def test_evaluates_definition_specific_timeouts(
        self,
        checker: NetworkTimeoutChecker,
        definition_specific_assignments: tuple[CheckerAssignment, CheckerAssignment],
    ) -> None:
        short_timeout, long_timeout = definition_specific_assignments

        judgments = await checker.judge(
            (short_timeout, long_timeout),
            context=IdleCheckerContext(
                current_time=_BASE_TIME + timedelta(seconds=20),
            ),
        )

        assert [judgment.checker_id for judgment in judgments] == [
            short_timeout.definition.checker_id,
            long_timeout.definition.checker_id,
        ]
        assert [judgment.status for judgment in judgments] == [
            IdleCheckPhase.IDLE_EXPIRED,
            IdleCheckPhase.IDLE,
        ]
