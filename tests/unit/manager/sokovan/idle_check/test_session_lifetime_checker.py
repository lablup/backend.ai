from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData
from ai.backend.manager.sokovan.idle_check.checkers.base import CheckerAssignment
from ai.backend.manager.sokovan.idle_check.checkers.session_lifetime import (
    SessionLifetimeChecker,
)

_BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)


class SessionFactory(Protocol):
    def __call__(
        self,
        *,
        starts_at: datetime | None = _BASE_TIME,
        created_at: datetime = _BASE_TIME,
    ) -> IdleCheckSession: ...


class AssignmentFactory(Protocol):
    def __call__(
        self,
        *,
        max_lifetime_seconds: int,
        sessions: Sequence[IdleCheckSession],
    ) -> CheckerAssignment: ...


class TestSessionLifetimeSpec:
    def test_accepts_zero_as_disabled_lifetime(self) -> None:
        spec = SessionLifetimeSpec(max_lifetime_seconds=0)

        assert spec.max_lifetime_seconds == 0

    def test_rejects_negative_lifetime(self) -> None:
        with pytest.raises(ValidationError):
            SessionLifetimeSpec(max_lifetime_seconds=-1)


class TestSessionLifetimeChecker:
    @pytest.fixture()
    def checker(self) -> SessionLifetimeChecker:
        return SessionLifetimeChecker()

    @pytest.fixture()
    def session_factory(self) -> SessionFactory:
        def create_session(
            *,
            starts_at: datetime | None = _BASE_TIME,
            created_at: datetime = _BASE_TIME,
        ) -> IdleCheckSession:
            return IdleCheckSession(
                session_id=SessionId(uuid4()),
                created_at=created_at,
                starts_at=starts_at,
            )

        return create_session

    @pytest.fixture()
    def assignment_factory(self) -> AssignmentFactory:
        def create_assignment(
            *,
            max_lifetime_seconds: int,
            sessions: Sequence[IdleCheckSession],
        ) -> CheckerAssignment:
            return CheckerAssignment(
                definition=IdleCheckerDefinitionData(
                    checker_id=IdleCheckerID(uuid4()),
                    checker_type=CheckerType.SESSION_LIFETIME,
                    target_session_types=frozenset({SessionTypes.INTERACTIVE}),
                    spec=IdleCheckerSpec(
                        type=CheckerType.SESSION_LIFETIME,
                        session_lifetime=SessionLifetimeSpec(
                            max_lifetime_seconds=max_lifetime_seconds
                        ),
                    ),
                ),
                sessions=sessions,
            )

        return create_assignment

    async def test_session_before_deadline_is_active(
        self,
        checker: SessionLifetimeChecker,
        session_factory: SessionFactory,
        assignment_factory: AssignmentFactory,
    ) -> None:
        session = session_factory()
        assignment = assignment_factory(max_lifetime_seconds=30, sessions=(session,))

        judgments = await checker.judge(
            (assignment,), current_time=_BASE_TIME + timedelta(seconds=29)
        )

        assert len(judgments) == 1
        assert judgments[0].session_id == session.session_id
        assert judgments[0].is_idle is False

    async def test_session_at_deadline_is_idle(
        self,
        checker: SessionLifetimeChecker,
        session_factory: SessionFactory,
        assignment_factory: AssignmentFactory,
    ) -> None:
        session = session_factory()
        assignment = assignment_factory(max_lifetime_seconds=30, sessions=(session,))

        judgments = await checker.judge(
            (assignment,), current_time=_BASE_TIME + timedelta(seconds=30)
        )

        assert len(judgments) == 1
        assert judgments[0].session_id == session.session_id
        assert judgments[0].is_idle is True
        assert judgments[0].message == (
            "Session lifetime exceeded: max_lifetime_seconds=30, running_seconds=30"
        )

    async def test_session_after_deadline_is_idle(
        self,
        checker: SessionLifetimeChecker,
        session_factory: SessionFactory,
        assignment_factory: AssignmentFactory,
    ) -> None:
        session = session_factory()
        assignment = assignment_factory(max_lifetime_seconds=30, sessions=(session,))

        judgments = await checker.judge(
            (assignment,), current_time=_BASE_TIME + timedelta(seconds=31.2)
        )

        assert judgments[0].is_idle is True
        assert judgments[0].message == (
            "Session lifetime exceeded: max_lifetime_seconds=30, running_seconds=31.2"
        )

    async def test_disabled_lifetime_skips_assignment(
        self,
        checker: SessionLifetimeChecker,
        session_factory: SessionFactory,
        assignment_factory: AssignmentFactory,
    ) -> None:
        assignment = assignment_factory(
            max_lifetime_seconds=0,
            sessions=(session_factory(),),
        )

        judgments = await checker.judge((assignment,), current_time=_BASE_TIME + timedelta(days=1))

        assert judgments == []

    async def test_excludes_session_when_starts_at_is_missing(
        self,
        checker: SessionLifetimeChecker,
        session_factory: SessionFactory,
        assignment_factory: AssignmentFactory,
    ) -> None:
        session = session_factory(
            starts_at=None,
            created_at=_BASE_TIME - timedelta(seconds=30),
        )
        assignment = assignment_factory(max_lifetime_seconds=30, sessions=(session,))

        judgments = await checker.judge((assignment,), current_time=_BASE_TIME)

        assert judgments == []

    async def test_evaluates_multiple_definitions_independently(
        self,
        checker: SessionLifetimeChecker,
        session_factory: SessionFactory,
        assignment_factory: AssignmentFactory,
    ) -> None:
        session = session_factory()
        short_lifetime = assignment_factory(max_lifetime_seconds=10, sessions=(session,))
        long_lifetime = assignment_factory(max_lifetime_seconds=30, sessions=(session,))

        judgments = await checker.judge(
            (short_lifetime, long_lifetime),
            current_time=_BASE_TIME + timedelta(seconds=20),
        )

        assert [judgment.checker_id for judgment in judgments] == [
            short_lifetime.definition.checker_id,
            long_lifetime.definition.checker_id,
        ]
        assert [judgment.is_idle for judgment in judgments] == [True, False]

    async def test_evaluates_every_session_in_assignment(
        self,
        checker: SessionLifetimeChecker,
        session_factory: SessionFactory,
        assignment_factory: AssignmentFactory,
    ) -> None:
        expired_session = session_factory(starts_at=_BASE_TIME - timedelta(seconds=30))
        active_session = session_factory(starts_at=_BASE_TIME - timedelta(seconds=10))
        assignment = assignment_factory(
            max_lifetime_seconds=20,
            sessions=(expired_session, active_session),
        )

        judgments = await checker.judge((assignment,), current_time=_BASE_TIME)

        assert [judgment.session_id for judgment in judgments] == [
            expired_session.session_id,
            active_session.session_id,
        ]
        assert [judgment.is_idle for judgment in judgments] == [True, False]

    async def test_rejects_assignment_with_mismatched_spec(
        self,
        checker: SessionLifetimeChecker,
        session_factory: SessionFactory,
    ) -> None:
        assignment = CheckerAssignment(
            definition=IdleCheckerDefinitionData(
                checker_id=IdleCheckerID(uuid4()),
                checker_type=CheckerType.SESSION_LIFETIME,
                target_session_types=frozenset({SessionTypes.INTERACTIVE}),
                spec=IdleCheckerSpec(
                    type=CheckerType.NETWORK_TIMEOUT,
                    network=NetworkTimeoutSpec(),
                ),
            ),
            sessions=(session_factory(),),
        )

        with pytest.raises(InternalServerError):
            await checker.judge((assignment,), current_time=_BASE_TIME)
