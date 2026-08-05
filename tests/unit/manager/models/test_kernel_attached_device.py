"""Constraint tests for the kernel_attached_devices table (BA-7178).

Verifies the schema contract: composite PK uniqueness, the kernels FK
cascade, and lossless round-trip of the raw plugin capacity map in ``data``.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.exc import IntegrityError

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import KernelId, ResourceSlot, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.base import DeviceCapacityEntry
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.kernel_attached_device.row import KernelAttachedDeviceRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables


class TestKernelAttachedDevice:
    @pytest.fixture
    async def database_with_tables(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                ProjectResourcePolicyRow,
                GroupRow,
                AgentRow,
                ContainerRegistryRow,
                ImageRow,
                SessionRow,
                KernelRow,
                KernelAttachedDeviceRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def kernel_id(
        self, database_with_tables: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[KernelId, None]:
        """Create the FK-complete row chain down to a single kernel."""
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        sgroup_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        sgroup_id = ResourceGroupID(uuid.uuid4())
        group_id = uuid.uuid4()
        session_id = SessionId(uuid.uuid4())
        new_kernel_id = KernelId(uuid.uuid4())

        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(DomainRow(id=domain_id, name=domain_name))
            db_sess.add(
                ScalingGroupRow(
                    id=sgroup_id,
                    name=sgroup_name,
                    driver="static",
                    scheduler="fifo",
                )
            )
            policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=5,
                )
            )
            await db_sess.flush()
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    resource_policy=policy_name,
                )
            )
            await db_sess.flush()
            db_sess.add(
                SessionRow(
                    id=session_id,
                    name=f"test-session-{uuid.uuid4().hex[:8]}",
                    user_uuid=uuid.uuid4(),
                    group_id=group_id,
                    domain_id=domain_id,
                    domain_name=domain_name,
                    resource_group_id=sgroup_id,
                    scaling_group_name=sgroup_name,
                    status=SessionStatus.RUNNING,
                    occupying_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    vfolder_mounts=[],
                )
            )
            await db_sess.flush()
            db_sess.add(
                KernelRow(
                    id=new_kernel_id,
                    session_id=session_id,
                    scaling_group=sgroup_name,
                    resource_group_id=sgroup_id,
                    cluster_hostname=f"kernel-{uuid.uuid4().hex[:8]}",
                    image="python:3.8",
                    architecture="x86_64",
                    registry="docker.io",
                    status=KernelStatus.RUNNING,
                    status_changed=datetime.now(tzutc()),
                    occupied_slots=ResourceSlot(),
                    requested_slots=ResourceSlot(),
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=uuid.uuid4(),
                    access_key="test-access-key",
                    mounts=[],
                    environ={},
                    vfolder_mounts=[],
                    preopen_ports=[],
                    repl_in_port=2001,
                    repl_out_port=2002,
                    stdin_port=2003,
                    stdout_port=2004,
                )
            )
            await db_sess.flush()

        yield new_kernel_id

    async def test_insert_and_read_back(
        self,
        database_with_tables: ExtendedAsyncSAEngine,
        kernel_id: KernelId,
    ) -> None:
        """Rows round-trip with model_name and the capacity entries preserved."""
        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(
                KernelAttachedDeviceRow(
                    kernel_id=kernel_id,
                    device_name="cuda",
                    device_id="GPU-1",
                    model_name="NVIDIA H100",
                    data=[
                        DeviceCapacityEntry(name="smp", value=8),
                        DeviceCapacityEntry(name="mem", value=81920),
                    ],
                )
            )
            db_sess.add(
                KernelAttachedDeviceRow(
                    kernel_id=kernel_id,
                    device_name="cpu",
                    device_id="0",
                    model_name="",
                )
            )
            await db_sess.flush()

        async with database_with_tables.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(KernelAttachedDeviceRow)
                .where(KernelAttachedDeviceRow.kernel_id == kernel_id)
                .order_by(KernelAttachedDeviceRow.device_name)
            )
            rows = result.scalars().all()

        assert len(rows) == 2
        cpu_row, cuda_row = rows
        assert cuda_row.model_name == "NVIDIA H100"
        assert cuda_row.data == [
            DeviceCapacityEntry(name="smp", value=8),
            DeviceCapacityEntry(name="mem", value=81920),
        ]
        assert cuda_row.created_at is not None
        assert cpu_row.data == []

    async def test_duplicate_pk_raises_integrity_error(
        self,
        database_with_tables: ExtendedAsyncSAEngine,
        kernel_id: KernelId,
    ) -> None:
        """A second row with the same (kernel_id, device_name, device_id) violates the PK."""
        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(
                KernelAttachedDeviceRow(
                    kernel_id=kernel_id,
                    device_name="cuda",
                    device_id="GPU-1",
                    model_name="NVIDIA H100",
                )
            )
            await db_sess.flush()

        with pytest.raises(IntegrityError):
            async with database_with_tables.begin_session() as db_sess:
                db_sess.add(
                    KernelAttachedDeviceRow(
                        kernel_id=kernel_id,
                        device_name="cuda",
                        device_id="GPU-1",
                        model_name="duplicate",
                    )
                )
                await db_sess.flush()

    async def test_kernel_delete_cascades(
        self,
        database_with_tables: ExtendedAsyncSAEngine,
        kernel_id: KernelId,
    ) -> None:
        """Deleting the kernel removes its device rows via ON DELETE CASCADE."""
        async with database_with_tables.begin_session() as db_sess:
            db_sess.add(
                KernelAttachedDeviceRow(
                    kernel_id=kernel_id,
                    device_name="cuda",
                    device_id="GPU-1",
                    model_name="NVIDIA H100",
                )
            )
            await db_sess.flush()

        async with database_with_tables.begin_session() as db_sess:
            await db_sess.execute(sa.delete(KernelRow).where(KernelRow.id == kernel_id))

        async with database_with_tables.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.select(sa.func.count())
                .select_from(KernelAttachedDeviceRow)
                .where(KernelAttachedDeviceRow.kernel_id == kernel_id)
            )
            assert result.scalar_one() == 0
