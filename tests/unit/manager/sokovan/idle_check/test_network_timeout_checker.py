from __future__ import annotations

from collections.abc import Sequence
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
_BASE_TIMESTAMP = str(_BASE_TIME.timestamp()).encode("utf-8")


class AssignmentFactory(Protocol):
    def __call__(
        self,
        *,
        idle_timeout_seconds: int,
        sessions: Sequence[IdleCheckSession],
    ) -> CheckerAssignment: ...


class TestNetworkTimeoutSpec:
    def test_accepts_zero_as_disabled_timeout(self) -> None:
        spec = NetworkTimeoutSpec(idle_timeout_seconds=0)

        assert spec.idle_timeout_seconds == 0

    def test_rejects_negative_timeout(self) -> None:
        with pytest.raises(ValidationError):
            NetworkTimeoutSpec(idle_timeout_seconds=-1)


class TestNetworkTimeoutChecker:
    @pytest.fixture()
    def valkey_live(self) -> AsyncMock:
        def count_active_connections(session_ids: Sequence[str]) -> dict[str, int]:
            return dict.fromkeys(session_ids, 0)

        client = AsyncMock(spec=ValkeyLiveClient)
        client.get_multiple_live_data.return_value = [_BASE_TIMESTAMP]
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
        )

    @pytest.fixture()
    def assignment_factory(self) -> AssignmentFactory:
        def create_assignment(
            *,
            idle_timeout_seconds: int,
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
                            idle_timeout_seconds=idle_timeout_seconds,
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
        return assignment_factory(idle_timeout_seconds=30, sessions=(session,))

    @pytest.fixture()
    def active_connection_valkey(
        self,
        valkey_live: AsyncMock,
        session: IdleCheckSession,
    ) -> AsyncMock:
        valkey_live.count_active_connections_batch.side_effect = lambda _session_ids: {
            str(session.session_id): 1
        }
        return valkey_live

    @pytest.fixture(params=[None, b"0"])
    def unavailable_last_access_valkey(
        self,
        request: pytest.FixtureRequest,
        valkey_live: AsyncMock,
    ) -> AsyncMock:
        valkey_live.get_multiple_live_data.return_value = [request.param]
        return valkey_live

    @pytest.fixture()
    def disabled_assignment(
        self,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
    ) -> CheckerAssignment:
        return assignment_factory(idle_timeout_seconds=0, sessions=(session,))

    @pytest.fixture()
    def definition_specific_assignments(
        self,
        session: IdleCheckSession,
        assignment_factory: AssignmentFactory,
    ) -> tuple[CheckerAssignment, CheckerAssignment]:
        return (
            assignment_factory(idle_timeout_seconds=10, sessions=(session,)),
            assignment_factory(idle_timeout_seconds=30, sessions=(session,)),
        )

    async def test_session_before_timeout_is_active(
        self,
        checker: NetworkTimeoutChecker,
        session: IdleCheckSession,
        assignment: CheckerAssignment,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=29)),
        )

        assert len(judgments) == 1
        assert judgments[0].session_id == session.session_id
        assert judgments[0].is_idle is False

    async def test_session_at_timeout_is_idle(
        self,
        checker: NetworkTimeoutChecker,
        assignment: CheckerAssignment,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=30)),
        )

        assert judgments[0].is_idle is True
        assert "last_access_at=2026-01-01 00:00:00 UTC" in judgments[0].message

    async def test_session_after_timeout_is_idle(
        self,
        checker: NetworkTimeoutChecker,
        assignment: CheckerAssignment,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(seconds=31.2)),
        )

        assert judgments[0].is_idle is True

    async def test_active_connection_keeps_stale_session_active(
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

        assert judgments[0].is_idle is False

    async def test_missing_or_disabled_last_access_skips_judgment(
        self,
        checker: NetworkTimeoutChecker,
        assignment: CheckerAssignment,
        unavailable_last_access_valkey: AsyncMock,
    ) -> None:
        judgments = await checker.judge(
            (assignment,),
            context=IdleCheckerContext(
                current_time=_BASE_TIME + timedelta(seconds=60),
            ),
        )

        assert judgments == []

    async def test_disabled_timeout_skips_assignment(
        self,
        checker: NetworkTimeoutChecker,
        disabled_assignment: CheckerAssignment,
    ) -> None:
        judgments = await checker.judge(
            (disabled_assignment,),
            context=IdleCheckerContext(current_time=_BASE_TIME + timedelta(days=1)),
        )

        assert judgments == []

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
        assert [judgment.is_idle for judgment in judgments] == [True, False]
