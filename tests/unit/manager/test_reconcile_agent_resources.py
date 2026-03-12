"""Tests for AgentRegistry._reconcile_agent_resources()."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ResourceSlot, SlotName
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, create_async_engine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.testutils.db import with_tables


class TestReconcileAgentResources:
    """Tests for AgentRegistry._reconcile_agent_resources()."""

    @pytest.fixture
    async def database_connection(
        self,
        postgres_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        _, addr = postgres_container
        url = f"postgresql+asyncpg://postgres:develove@{addr.host}:{addr.port}/testing"
        engine = create_async_engine(
            url,
            pool_size=8,
            pool_pre_ping=False,
            max_overflow=64,
        )
        yield engine
        await engine.dispose()

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                ScalingGroupRow,
                GroupRow,
                AgentRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
                AgentResourceRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def registry(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[AgentRegistry, None]:
        mock_config: MagicMock = MagicMock()
        mock_config.config.network.rpc.keepalive_timeout = 30

        with (
            patch("ai.backend.manager.registry.aiodocker.Docker"),
            patch("ai.backend.manager.registry.SessionLifecycleManager"),
        ):
            reg = AgentRegistry(
                config_provider=mock_config,
                db=db_with_tables,
                agent_cache=MagicMock(),
                agent_client_pool=MagicMock(),
                valkey_stat=MagicMock(),
                valkey_live=MagicMock(),
                valkey_image=MagicMock(),
                event_producer=MagicMock(),
                event_hub=MagicMock(),
                storage_manager=MagicMock(),
                hook_plugin_ctx=MagicMock(),
                network_plugin_ctx=MagicMock(),
                scheduling_controller=MagicMock(),
                manager_public_key=PublicKey(b"GqK]ZYY#h*9jAQbGxSwkeZX3Y*%b+DiY$7ju6sh{"),
                manager_secret_key=SecretKey(b"37KX6]ac^&hcnSaVo=-%eVO9M]ENe8v=BOWF(Sw$"),
            )
        await reg.init()
        try:
            yield reg
        finally:
            await reg.shutdown()

    async def _seed_slot_types(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count", rank=0))
            db_sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes", rank=1))

    async def _seed_infrastructure(self, db: ExtendedAsyncSAEngine) -> tuple[str, uuid.UUID, str]:
        """Create domain, project, scaling group, and agent."""
        domain_name = "test-domain"
        project_id = uuid4()
        sg_name = "test-sg"
        agent_id = "i-test-agent"
        async with db.begin_session() as db_sess:
            db_sess.add(DomainRow(name=domain_name))
        async with db.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=0,
                    max_network_count=5,
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=sg_name,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name="test-project",
                    domain_name=domain_name,
                    resource_policy="default",
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=AgentStatus.ALIVE,
                    status_changed=datetime.now(tzutc()),
                    region="test-region",
                    scaling_group=sg_name,
                    available_slots=ResourceSlot({SlotName("cpu"): "8", SlotName("mem"): "32768"}),
                    occupied_slots=ResourceSlot({}),
                    addr="tcp://127.0.0.1:6001",
                    version="24.12.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )
        return domain_name, project_id, agent_id

    async def _seed_agent_resources(
        self,
        db: ExtendedAsyncSAEngine,
        agent_id: str,
        resources: dict[str, tuple[Decimal, Decimal]],
    ) -> None:
        """Seed agent_resources rows. resources: slot_name → (capacity, used)."""
        async with db.begin_session() as db_sess:
            for slot_name, (capacity, used) in resources.items():
                db_sess.add(
                    AgentResourceRow(
                        agent_id=agent_id,
                        slot_name=slot_name,
                        capacity=capacity,
                        used=used,
                    )
                )

    async def _create_kernel_with_allocations(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        domain_name: str,
        project_id: uuid.UUID,
        agent_id: str,
        status: KernelStatus,
        allocations: dict[str, tuple[Decimal, Decimal | None]],
        free_at: datetime | None = None,
    ) -> uuid.UUID:
        session_id = uuid4()
        kernel_id = uuid4()
        empty_slots = ResourceSlot({})
        async with db.begin_session() as db_sess:
            db_sess.add(
                SessionRow(
                    id=session_id,
                    domain_name=domain_name,
                    group_id=project_id,
                    user_uuid=uuid4(),
                    occupying_slots=empty_slots,
                    requested_slots=empty_slots,
                )
            )
            await db_sess.flush()
            db_sess.add(
                KernelRow(
                    id=kernel_id,
                    session_id=session_id,
                    domain_name=domain_name,
                    group_id=project_id,
                    user_uuid=uuid4(),
                    status=status,
                    occupied_slots=empty_slots,
                    requested_slots=empty_slots,
                    repl_in_port=0,
                    repl_out_port=0,
                    stdin_port=0,
                    stdout_port=0,
                    scaling_group="test-sg",
                    agent=agent_id,
                )
            )
            await db_sess.flush()
            for slot_name, (requested, used) in allocations.items():
                db_sess.add(
                    ResourceAllocationRow(
                        kernel_id=kernel_id,
                        slot_name=slot_name,
                        requested=requested,
                        used=used,
                        free_at=free_at,
                    )
                )
        return kernel_id

    async def _get_agent_resource_used(
        self,
        db: ExtendedAsyncSAEngine,
        agent_id: str,
    ) -> dict[str, Decimal]:
        """Read current agent_resources.used values."""
        ar = AgentResourceRow.__table__
        async with db.begin_session() as db_sess:
            rows = (
                await db_sess.execute(
                    sa.select(ar.c.slot_name, ar.c.used).where(ar.c.agent_id == agent_id)
                )
            ).all()
        return {row.slot_name: row.used for row in rows}

    async def test_no_drift_no_corrections(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        registry: AgentRegistry,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When agent_resources.used matches actual allocations, no corrections are made."""
        db = db_with_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(db)

        # Actual usage: cpu=2, mem=1024
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            status=KernelStatus.RUNNING,
            allocations={
                "cpu": (Decimal("2"), Decimal("2")),
                "mem": (Decimal("1024"), Decimal("1024")),
            },
        )

        # Set agent_resources.used to match actual
        await self._seed_agent_resources(
            db,
            agent_id,
            {
                "cpu": (Decimal("8"), Decimal("2")),
                "mem": (Decimal("32768"), Decimal("1024")),
            },
        )

        with caplog.at_level(logging.WARNING):
            await registry._reconcile_agent_resources()

        assert "agent_resources drift detected" not in caplog.text

        used = await self._get_agent_resource_used(db, agent_id)
        assert used["cpu"] == Decimal("2")
        assert used["mem"] == Decimal("1024")

    async def test_over_count_corrected_down(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        registry: AgentRegistry,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When agent_resources.used > actual, it is corrected down."""
        db = db_with_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(db)

        # Actual usage: cpu=2
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            status=KernelStatus.RUNNING,
            allocations={"cpu": (Decimal("2"), Decimal("2"))},
        )

        # Tracked as 100 but actual is 2
        await self._seed_agent_resources(
            db,
            agent_id,
            {
                "cpu": (Decimal("200"), Decimal("100")),
            },
        )

        with caplog.at_level(logging.WARNING):
            await registry._reconcile_agent_resources()

        assert "agent_resources drift detected" in caplog.text
        assert agent_id in caplog.text

        used = await self._get_agent_resource_used(db, agent_id)
        assert used["cpu"] == Decimal("2")

    async def test_under_count_corrected_up(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        registry: AgentRegistry,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When agent_resources.used < actual, it is corrected up."""
        db = db_with_tables
        await self._seed_slot_types(db)
        domain_name, project_id, agent_id = await self._seed_infrastructure(db)

        # Actual usage: cpu=6 (two kernels)
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            status=KernelStatus.RUNNING,
            allocations={"cpu": (Decimal("4"), Decimal("4"))},
        )
        await self._create_kernel_with_allocations(
            db,
            domain_name=domain_name,
            project_id=project_id,
            agent_id=agent_id,
            status=KernelStatus.RUNNING,
            allocations={"cpu": (Decimal("2"), Decimal("2"))},
        )

        # Tracked as 1 but actual is 6
        await self._seed_agent_resources(
            db,
            agent_id,
            {
                "cpu": (Decimal("8"), Decimal("1")),
            },
        )

        with caplog.at_level(logging.WARNING):
            await registry._reconcile_agent_resources()

        assert "agent_resources drift detected" in caplog.text

        used = await self._get_agent_resource_used(db, agent_id)
        assert used["cpu"] == Decimal("6")

    async def test_no_allocations_resets_used_to_zero(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        registry: AgentRegistry,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When there are no active allocations but used > 0, it is corrected to 0."""
        db = db_with_tables
        await self._seed_slot_types(db)
        domain_name, _, agent_id = await self._seed_infrastructure(db)

        # No allocations exist, but agent_resources says used=50
        await self._seed_agent_resources(
            db,
            agent_id,
            {
                "cpu": (Decimal("8"), Decimal("50")),
            },
        )

        with caplog.at_level(logging.WARNING):
            await registry._reconcile_agent_resources()

        assert "agent_resources drift detected" in caplog.text

        used = await self._get_agent_resource_used(db, agent_id)
        assert used["cpu"] == Decimal("0")
