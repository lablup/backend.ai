from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.identifier.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.types import KernelId, ResourceSlot
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.api.adapters.scheduling_history.adapter import SchedulingHistoryAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api.rest.scheduling_history.handler import SchedulingHistoryHandler
from ai.backend.manager.api.rest.scheduling_history.registry import (
    register_scheduling_history_routes,
)
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.scheduling_history.handler import V2SchedulingHistoryHandler
from ai.backend.manager.api.rest.v2.scheduling_history.registry import (
    register_v2_scheduling_history_routes,
)
from ai.backend.manager.data.kernel.types import KernelSchedulingPhase
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.scheduling_history.row import KernelSchedulingHistoryRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduling_history.repository import (
    SchedulingHistoryRepository,
)
from ai.backend.manager.services.scheduling_history.processors import SchedulingHistoryProcessors
from ai.backend.manager.services.scheduling_history.service import SchedulingHistoryService
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


@pytest.fixture()
def scheduling_history_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> SchedulingHistoryProcessors:
    repo = SchedulingHistoryRepository(database_engine)
    service = SchedulingHistoryService(repo)
    return SchedulingHistoryProcessors(
        service=service,
        action_monitors=[],
        validators=ActionValidators(
            rbac=RBACValidators(scope=AsyncMock(), single_entity=AsyncMock(), bulk=AsyncMock()),
        ),
    )


@pytest.fixture()
def scheduling_history_adapter(
    scheduling_history_processors: SchedulingHistoryProcessors,
) -> SchedulingHistoryAdapter:
    """Build an adapter wired only with scheduling-history processors.

    Every call site in the adapter goes through ``self._processors.scheduling_history``,
    so a MagicMock backing object with that attribute set is sufficient.
    """
    processors = MagicMock()
    processors.scheduling_history = scheduling_history_processors
    return SchedulingHistoryAdapter(processors)


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    scheduling_history_processors: SchedulingHistoryProcessors,
    scheduling_history_adapter: SchedulingHistoryAdapter,
) -> list[RouteRegistry]:
    """Load both v1 and v2 scheduling-history route trees."""
    v2_registry = RouteRegistry.create("v2", route_deps.cors_options)
    v2_registry.add_subregistry(
        register_v2_scheduling_history_routes(
            V2SchedulingHistoryHandler(adapter=scheduling_history_adapter),
            route_deps,
        )
    )
    return [
        register_scheduling_history_routes(
            SchedulingHistoryHandler(scheduling_history=scheduling_history_processors),
            route_deps,
        ),
        v2_registry,
    ]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@dataclass(frozen=True)
class KernelHistorySeed:
    """Identifiers of the seeded kernels and the history rows attached to them."""

    session_id: SessionID
    kernel_id: KernelId
    other_kernel_id: KernelId
    history_ids: list[KernelSchedulingHistoryID]
    other_history_id: KernelSchedulingHistoryID


@dataclass(frozen=True)
class _HistoryRowSeed:
    """One ``kernel_scheduling_history`` row to seed, before ids/timestamps are attached.

    ``phase`` is a free-form string in the domain model (a ``ScheduleType`` value); the
    transition statuses and result are enum-typed.
    """

    phase: str
    from_status: KernelSchedulingPhase
    to_status: KernelSchedulingPhase
    result: SchedulingResult
    attempts: int


@pytest.fixture()
async def kernel_history_seed(
    database_engine: ExtendedAsyncSAEngine,
    domain_fixture: DomainFixtureData,
    group_fixture: uuid.UUID,
    scaling_group_name: ResourceGroupName,
    scaling_group_id: ResourceGroupID,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[KernelHistorySeed]:
    """Seed one session with two kernels: three history rows on the first, one on the second.

    ``kernel_scheduling_history`` has no writer yet (BA-6852), so the rows go in directly.
    The scoped endpoint runs an existence check against ``kernels``, hence the real kernel rows.
    """
    session_id = SessionID(uuid.uuid4())
    kernel_id = KernelId(uuid.uuid4())
    other_kernel_id = KernelId(uuid.uuid4())
    slots = ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1073741824")})
    now = datetime.now(tz=UTC)

    # created_at is staggered so ordering and cursor pagination are deterministic.
    row_seeds = [
        _HistoryRowSeed(
            phase="PREPARING",
            from_status=KernelSchedulingPhase.PREPARING,
            to_status=KernelSchedulingPhase.PULLING,
            result=SchedulingResult.SUCCESS,
            attempts=1,
        ),
        _HistoryRowSeed(
            phase="PULLING",
            from_status=KernelSchedulingPhase.PULLING,
            to_status=KernelSchedulingPhase.PREPARED,
            result=SchedulingResult.SUCCESS,
            attempts=2,
        ),
        _HistoryRowSeed(
            phase="RUNNING",
            from_status=KernelSchedulingPhase.CREATING,
            to_status=KernelSchedulingPhase.RUNNING,
            result=SchedulingResult.FAILURE,
            attempts=3,
        ),
    ]
    history_ids = [KernelSchedulingHistoryID(uuid.uuid4()) for _ in row_seeds]
    other_history_id = KernelSchedulingHistoryID(uuid.uuid4())

    async with database_engine.begin_session() as db_sess:
        db_sess.add(
            SessionRow(
                id=session_id,
                name=f"session-{session_id.hex[:8]}",
                domain_name=domain_fixture.domain_name,
                domain_id=domain_fixture.domain_id,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                scaling_group_name=scaling_group_name,
                resource_group_id=scaling_group_id,
                occupying_slots=slots,
                requested_slots=slots,
            )
        )
        await db_sess.flush()
        db_sess.add_all([
            KernelRow(
                id=kid,
                session_id=session_id,
                domain_name=domain_fixture.domain_name,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                occupied_slots=slots,
                requested_slots=slots,
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                scaling_group=scaling_group_name,
                resource_group_id=scaling_group_id,
            )
            for kid in (kernel_id, other_kernel_id)
        ])
        await db_sess.flush()

        for offset, (hid, seed) in enumerate(zip(history_ids, row_seeds, strict=False)):
            db_sess.add(
                KernelSchedulingHistoryRow(
                    id=hid,
                    kernel_id=kernel_id,
                    session_id=session_id,
                    phase=seed.phase,
                    from_status=seed.from_status,
                    to_status=seed.to_status,
                    result=seed.result,
                    error_code=(
                        None if seed.result is SchedulingResult.SUCCESS else "ERR_KERNEL_START"
                    ),
                    message=f"{seed.phase} transition",
                    attempts=seed.attempts,
                    created_at=now + timedelta(seconds=offset),
                    updated_at=now + timedelta(seconds=offset),
                )
            )
        db_sess.add(
            KernelSchedulingHistoryRow(
                id=other_history_id,
                kernel_id=other_kernel_id,
                session_id=session_id,
                phase="PREPARING",
                from_status=KernelSchedulingPhase.PREPARING,
                to_status=KernelSchedulingPhase.PULLING,
                result=SchedulingResult.SUCCESS,
                error_code=None,
                message="other kernel transition",
                attempts=1,
                created_at=now,
                updated_at=now,
            )
        )

    yield KernelHistorySeed(
        session_id=session_id,
        kernel_id=kernel_id,
        other_kernel_id=other_kernel_id,
        history_ids=history_ids,
        other_history_id=other_history_id,
    )

    async with database_engine.begin() as conn:
        await conn.execute(
            sa.delete(KernelSchedulingHistoryRow).where(
                KernelSchedulingHistoryRow.session_id == session_id
            )
        )
        await conn.execute(sa.delete(KernelRow).where(KernelRow.session_id == session_id))
        await conn.execute(sa.delete(SessionRow).where(SessionRow.id == session_id))
