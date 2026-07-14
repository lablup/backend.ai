from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.exceptions import NotFoundError, ServerError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.session.request import (
    RestartSessionRequest,
)
from ai.backend.common.dto.manager.session.response import (
    GetStatusHistoryResponse,
)
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import SessionSeedData, UserFixtureData


def _build_kernel_values(
    *,
    session_id: SessionId,
    unique: str,
    session_name: str,
    cluster_size: int,
    domain_name: str,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
    access_key: str,
    scaling_group: str,
    resource_group_id: ResourceGroupID,
    now: datetime,
) -> dict[str, Any]:
    """Return the common kernel column values shared by all session seed fixtures."""
    return dict(
        session_id=session_id,
        session_creation_id=f"cid-{unique}",
        session_name=session_name,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode="single-node",
        cluster_size=cluster_size,
        domain_name=domain_name,
        group_id=group_id,
        user_uuid=user_uuid,
        access_key=access_key,
        scaling_group=scaling_group,
        resource_group_id=resource_group_id,
        status_info="",
        occupied_slots=ResourceSlot(),
        requested_slots=ResourceSlot(),
        repl_in_port=0,
        repl_out_port=0,
        stdin_port=0,
        stdout_port=0,
        created_at=now,
    )


@pytest.fixture()
async def degraded_session_seed(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_name: ResourceGroupName,
    scaling_group_id: ResourceGroupID,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING_DEGRADED session with two kernels (one RUNNING, one ERROR)."""
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-degraded-{unique}"
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
        SessionStatus.RUNNING_DEGRADED.name: now.isoformat(),
    }

    common_kernel = _build_kernel_values(
        session_id=session_id,
        unique=unique,
        session_name=session_name,
        cluster_size=2,
        domain_name=domain_fixture.domain_name,
        group_id=group_fixture,
        user_uuid=admin_user_fixture.user_uuid,
        access_key=admin_user_fixture.keypair.access_key,
        scaling_group=scaling_group_name,
        resource_group_id=scaling_group_id,
        now=now,
    )

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=2,
                cluster_mode="single-node",
                domain_name=domain_fixture.domain_name,
                domain_id=domain_fixture.domain_id,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group_name=scaling_group_name,
                resource_group_id=scaling_group_id,
                status=SessionStatus.RUNNING_DEGRADED,
                status_info="",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=uuid.uuid4(),
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                status=KernelStatus.RUNNING,
                **common_kernel,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=uuid.uuid4(),
                cluster_role="sub",
                cluster_idx=1,
                cluster_hostname="sub1",
                status=KernelStatus.ERROR,
                **common_kernel,
            )
        )

    yield SessionSeedData(
        session_id=session_id,
        session_name=session_name,
        kernel_id=uuid.UUID(int=0),  # not meaningful for multi-kernel
        access_key=admin_user_fixture.keypair.access_key,
        domain_name=domain_fixture.domain_name,
        user_uuid=admin_user_fixture.user_uuid,
    )

    async with db_engine.begin() as conn:
        await conn.execute(kernels.delete().where(kernels.c.session_id == session_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


@pytest.fixture()
async def full_lifecycle_session_seed(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_name: ResourceGroupName,
    scaling_group_id: ResourceGroupID,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING session with a full lifecycle status_history
    (PENDING → SCHEDULED → PREPARING → PULLING → CREATING → RUNNING).
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-full-lifecycle-{unique}"
    kernel_id = uuid.uuid4()
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.SCHEDULED.name: now.isoformat(),
        SessionStatus.PREPARING.name: now.isoformat(),
        SessionStatus.PULLING.name: now.isoformat(),
        SessionStatus.CREATING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
    }

    common_kernel = _build_kernel_values(
        session_id=session_id,
        unique=unique,
        session_name=session_name,
        cluster_size=1,
        domain_name=domain_fixture.domain_name,
        group_id=group_fixture,
        user_uuid=admin_user_fixture.user_uuid,
        access_key=admin_user_fixture.keypair.access_key,
        scaling_group=scaling_group_name,
        resource_group_id=scaling_group_id,
        now=now,
    )

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=1,
                cluster_mode="single-node",
                domain_name=domain_fixture.domain_name,
                domain_id=domain_fixture.domain_id,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group_name=scaling_group_name,
                resource_group_id=scaling_group_id,
                status=SessionStatus.RUNNING,
                status_info="",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=kernel_id,
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                status=KernelStatus.RUNNING,
                **common_kernel,
            )
        )

    yield SessionSeedData(
        session_id=session_id,
        session_name=session_name,
        kernel_id=kernel_id,
        access_key=admin_user_fixture.keypair.access_key,
        domain_name=domain_fixture.domain_name,
        user_uuid=admin_user_fixture.user_uuid,
    )

    async with db_engine.begin() as conn:
        await conn.execute(kernels.delete().where(kernels.c.session_id == session_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


class TestSessionRestart:
    """Test session restart lifecycle.

    Session restart is no longer supported by the sokovan-driven session lifecycle;
    the endpoint remains as a stub that returns HTTP 501. See commit 882f961ed6.
    """

    async def test_restart_returns_not_implemented(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Any restart attempt now returns 501 Not Implemented regardless of state."""
        with pytest.raises(ServerError) as exc_info:
            await admin_registry.session.restart(
                session_seed.session_name,
                RestartSessionRequest(),
            )
        assert exc_info.value.args[0] == 501

    async def test_restart_terminated_session_returns_not_implemented(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        """Restart against a TERMINATED session still returns 501."""
        with pytest.raises(ServerError) as exc_info:
            await admin_registry.session.restart(
                terminated_session_seed.session_name,
                RestartSessionRequest(),
            )
        assert exc_info.value.args[0] == 501

    async def test_restart_nonexistent_session_returns_not_implemented(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Restart against a missing session returns 501 (endpoint is a stub)."""
        with pytest.raises(ServerError) as exc_info:
            await admin_registry.session.restart(
                "nonexistent-session-xyz-99999",
                RestartSessionRequest(),
            )
        assert exc_info.value.args[0] == 501


class TestSessionStatusHistory:
    """Test status history for sessions in different lifecycle stages."""

    async def test_running_session_has_pending_and_running_history(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin queries status history of a RUNNING session.

        The seeded session was created with PENDING -> RUNNING transitions.
        Verifies that both status entries are recorded in the history and
        returned by the get_status_history endpoint.
        """
        result = await admin_registry.session.get_status_history(
            session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        assert SessionStatus.PENDING.name in history
        assert SessionStatus.RUNNING.name in history

    async def test_terminated_session_status_history_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin queries status history of a TERMINATED session.

        The get_status_history handler resolves the session with
        allow_stale=False, so terminated sessions are treated as
        non-existent and return 404. This prevents querying history
        of stale sessions through this endpoint.
        """
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_status_history(
                terminated_session_seed.session_name,
            )

    async def test_user_gets_own_session_status_history(
        self,
        user_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user queries status history of their own RUNNING session.

        Verifies that the status history endpoint is accessible to
        non-admin users for sessions they own.
        """
        result = await user_registry.session.get_status_history(
            user_session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        assert SessionStatus.RUNNING.name in history

    async def test_user_cannot_access_admin_session_status_history(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user attempts to query status history of an admin-owned session.

        Verifies that ownership scoping applies to the status history
        endpoint — sessions not owned by the requester are not resolvable.
        """
        with pytest.raises((NotFoundError, BackendAPIError)):
            await user_registry.session.get_status_history(
                session_seed.session_name,
            )

    async def test_full_lifecycle_status_history(
        self,
        admin_registry: BackendAIClientRegistry,
        full_lifecycle_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin queries status history of a session that went through
        the full scheduling lifecycle (PENDING → SCHEDULED → PREPARING →
        PULLING → CREATING → RUNNING).

        Verifies that every intermediate status is recorded in the history
        with a timestamp, confirming that the status_history column
        accumulates entries across all transitions.
        """
        result = await admin_registry.session.get_status_history(
            full_lifecycle_session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        expected_statuses = [
            SessionStatus.PENDING,
            SessionStatus.SCHEDULED,
            SessionStatus.PREPARING,
            SessionStatus.PULLING,
            SessionStatus.CREATING,
            SessionStatus.RUNNING,
        ]
        for status in expected_statuses:
            assert status.name in history, f"{status.name} missing from status history"

    async def test_degraded_session_status_history_includes_degraded(
        self,
        admin_registry: BackendAIClientRegistry,
        degraded_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin queries status history of a RUNNING_DEGRADED session.

        Verifies that the RUNNING_DEGRADED status is recorded in the history,
        confirming that the transition from RUNNING to RUNNING_DEGRADED was tracked.
        """
        result = await admin_registry.session.get_status_history(
            degraded_session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        assert SessionStatus.RUNNING.name in history
        assert SessionStatus.RUNNING_DEGRADED.name in history
