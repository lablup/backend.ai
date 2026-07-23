from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    IdleCheckPhase,
    SessionLifetimeSpec,
)
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import (
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow, SessionIdleCheckRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class SessionIdleCheckFixture:
    session_id: SessionId
    checker_id: IdleCheckerID


class TestSessionIdleCheckRow:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                ProjectResourcePolicyRow,
                DomainRow,
                GroupRow,
                ScalingGroupRow,
                SessionRow,
                IdleCheckerRow,
                SessionIdleCheckRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def persisted_idle_check(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> SessionIdleCheckFixture:
        domain_id = DomainID(uuid.uuid4())
        project_id = uuid.uuid4()
        resource_group_id = ResourceGroupID(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())
        checker_id = IdleCheckerID(uuid.uuid4())
        created_at = datetime(2026, 1, 1, tzinfo=UTC)
        expire_at = datetime(2026, 1, 2, tzinfo=UTC)
        async with database.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="session-idle-check-policy",
                    max_vfolder_count=10,
                    max_quota_scope_size=1024,
                    max_network_count=10,
                )
            )
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name="session-idle-check-domain",
                    description=None,
                    is_active=True,
                )
            )
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name="session-idle-check-project",
                    description=None,
                    is_active=True,
                    domain_name="session-idle-check-domain",
                    resource_policy="session-idle-check-policy",
                )
            )
            db_sess.add(
                ScalingGroupRow(
                    id=resource_group_id,
                    name="session-idle-check-resource-group",
                    description=None,
                    is_active=True,
                    is_public=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    use_host_network=False,
                )
            )
            db_sess.add(
                SessionRow(
                    id=session_id,
                    creation_id=str(session_id)[:32],
                    name=f"session-{session_id}",
                    session_type=SessionTypes.INTERACTIVE,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    domain_name="session-idle-check-domain",
                    domain_id=domain_id,
                    resource_group_id=resource_group_id,
                    group_id=project_id,
                    user_uuid=uuid.uuid4(),
                    access_key=None,
                    tag=None,
                    status=SessionStatus.RUNNING,
                    status_info=None,
                    status_data=None,
                    status_history={},
                    result=SessionResult.UNDEFINED,
                    created_at=created_at,
                    terminated_at=None,
                    starts_at=created_at,
                    startup_command=None,
                    callback_url=None,
                    occupying_slots=ResourceSlot({"cpu": "1"}),
                    requested_slots=ResourceSlot({"cpu": "1"}),
                    vfolder_mounts=[],
                    environ=None,
                    bootstrap_script=None,
                    use_host_network=False,
                    scaling_group_name="session-idle-check-resource-group",
                )
            )
            db_sess.add(
                IdleCheckerRow(
                    id=checker_id,
                    name=f"checker-{checker_id}",
                    description=None,
                    checker_type=CheckerType.SESSION_LIFETIME,
                    target_session_types=[SessionTypes.INTERACTIVE],
                    spec=IdleCheckerSpec(
                        type=CheckerType.SESSION_LIFETIME,
                        session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
                    ),
                )
            )
            await db_sess.flush()
            db_sess.add(
                SessionIdleCheckRow(
                    session_id=session_id,
                    idle_checker_id=checker_id,
                    expire_at=expire_at,
                    last_status=IdleCheckPhase.ACTIVE,
                    last_message="The session is active.",
                )
            )
        return SessionIdleCheckFixture(session_id=session_id, checker_id=checker_id)

    async def test_persists_expire_at_and_updated_at(
        self,
        database: ExtendedAsyncSAEngine,
        persisted_idle_check: SessionIdleCheckFixture,
    ) -> None:
        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (persisted_idle_check.session_id, persisted_idle_check.checker_id),
            )
            checker_row = await db_sess.get(
                IdleCheckerRow,
                persisted_idle_check.checker_id,
            )

        assert row is not None
        assert row.expire_at == datetime(2026, 1, 2, tzinfo=UTC)
        assert row.last_status is IdleCheckPhase.ACTIVE
        assert row.updated_at is not None
        assert checker_row is not None
        assert checker_row.initial_grace_period_seconds == 0

    async def test_rejects_negative_initial_grace_period(
        self,
        database: ExtendedAsyncSAEngine,
    ) -> None:
        with pytest.raises(sa.exc.IntegrityError):
            async with database.begin_session() as db_sess:
                db_sess.add(
                    IdleCheckerRow(
                        id=IdleCheckerID(uuid.uuid4()),
                        name="negative-grace-period-checker",
                        description=None,
                        checker_type=CheckerType.SESSION_LIFETIME,
                        target_session_types=[SessionTypes.INTERACTIVE],
                        initial_grace_period_seconds=-1,
                        spec=IdleCheckerSpec(
                            type=CheckerType.SESSION_LIFETIME,
                            session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
                        ),
                    )
                )

    async def test_rejects_duplicate_session_checker_pair(
        self,
        database: ExtendedAsyncSAEngine,
        persisted_idle_check: SessionIdleCheckFixture,
    ) -> None:
        with pytest.raises(sa.exc.IntegrityError):
            async with database.begin_session() as db_sess:
                db_sess.add(
                    SessionIdleCheckRow(
                        session_id=persisted_idle_check.session_id,
                        idle_checker_id=persisted_idle_check.checker_id,
                        expire_at=datetime(2026, 1, 2, tzinfo=UTC),
                        last_status=IdleCheckPhase.ACTIVE,
                        last_message="The session is active.",
                    )
                )

    async def test_deleting_session_cascades_idle_check(
        self,
        database: ExtendedAsyncSAEngine,
        persisted_idle_check: SessionIdleCheckFixture,
    ) -> None:
        async with database.begin_session() as db_sess:
            await db_sess.execute(
                sa.delete(SessionRow).where(SessionRow.id == persisted_idle_check.session_id)
            )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (persisted_idle_check.session_id, persisted_idle_check.checker_id),
            )

        assert row is None

    async def test_deleting_checker_cascades_idle_check(
        self,
        database: ExtendedAsyncSAEngine,
        persisted_idle_check: SessionIdleCheckFixture,
    ) -> None:
        async with database.begin_session() as db_sess:
            await db_sess.execute(
                sa.delete(IdleCheckerRow).where(
                    IdleCheckerRow.id == persisted_idle_check.checker_id
                )
            )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(
                SessionIdleCheckRow,
                (persisted_idle_check.session_id, persisted_idle_check.checker_id),
            )

        assert row is None
