from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.types import AgentId, DeviceName, ResourceSlot, SlotName, SlotTypes
from ai.backend.manager.data.agent.types import (
    AgentData,
    AgentHeartbeatUpsert,
    AgentStatus,
)
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource


@pytest.fixture
def mock_db_engine() -> MagicMock:
    return MagicMock(spec=ExtendedAsyncSAEngine)


@pytest.fixture
def mock_db_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def db_source(mock_db_engine: MagicMock) -> AgentDBSource:
    return AgentDBSource(db=mock_db_engine)


@pytest.fixture
def sample_agent_info() -> AgentInfo:
    return AgentInfo(
        ip="192.168.1.100",
        version="24.12.0",
        scaling_group="default",
        available_resource_slots=ResourceSlot({
            SlotName("cpu"): "8",
            SlotName("mem"): "32768",
            SlotName("cuda.shares"): "4",
        }),
        slot_key_and_units={
            SlotName("cpu"): SlotTypes.COUNT,
            SlotName("mem"): SlotTypes.BYTES,
            SlotName("cuda.shares"): SlotTypes.COUNT,
        },
        compute_plugins={
            DeviceName("cpu"): {"brand": "Intel", "model": "Core i7"},
        },
        addr="tcp://192.168.1.100:6001",
        public_key=PublicKey(b"test-public-key"),
        public_host="192.168.1.100",
        images=b"\x82\xc4\x00\x00",  # msgpack compressed data
        region="us-west-1",
        architecture="x86_64",
        auto_terminate_abusing_kernel=False,
    )


@pytest.fixture
def sample_heartbeat_upsert(sample_agent_info: AgentInfo) -> AgentHeartbeatUpsert:
    agent_id = AgentId("agent-001")
    return AgentHeartbeatUpsert.from_agent_info(
        agent_id=agent_id,
        agent_info=sample_agent_info,
        heartbeat_received=datetime.now(tzutc()),
    )


class TestAgentDBSource:
    @pytest.mark.asyncio
    async def test_get_by_id_existing_agent(
        self,
        db_source: AgentDBSource,
        mock_db_engine: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        # Given
        agent_id = AgentId("agent-001")
        mock_agent_row = MagicMock(spec=AgentRow)
        mock_agent_data = AgentData(
            id=agent_id,
            status=AgentStatus.ALIVE,
            status_changed=datetime.now(tzutc()),
            region="us-west-1",
            scaling_group="default",
            available_slots=ResourceSlot({SlotName("cpu"): 8.0}),
            occupied_slots=ResourceSlot({}),
            addr="tcp://192.168.1.100:6001",
            architecture="x86_64",
            version="24.12.0",
            compute_plugins=[],
            first_contact=datetime.now(tzutc()),
            lost_at=None,
            public_host="192.168.1.100",
            public_key=PublicKey(b"test-public-key"),
            schedulable=True,
            auto_terminate_abusing_kernel=False,
        )
        mock_agent_row.to_data.return_value = mock_agent_data
        mock_db_session.scalar.return_value = mock_agent_row

        mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_db_session

        # When
        result = await db_source.get_by_id(agent_id)

        # Then
        assert result == mock_agent_data
        mock_db_session.scalar.assert_called_once()
        call_args = mock_db_session.scalar.call_args[0][0]
        assert str(call_args) == str(sa.select(AgentRow).where(AgentRow.id == agent_id))

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_agent(
        self,
        db_source: AgentDBSource,
        mock_db_engine: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        # Given
        agent_id = AgentId("nonexistent-agent")
        mock_db_session.scalar.return_value = None
        mock_db_engine.begin_readonly_session.return_value.__aenter__.return_value = mock_db_session

        # When
        result = await db_source.get_by_id(agent_id)

        # Then
        assert result is None
        mock_db_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_agent_with_state_new_agent(
        self,
        db_source: AgentDBSource,
        mock_db_engine: MagicMock,
        mock_db_session: AsyncMock,
        sample_heartbeat_upsert: AgentHeartbeatUpsert,
    ) -> None:
        # Given
        mock_scaling_group = MagicMock(spec=ScalingGroupRow)
        mock_db_session.scalar.side_effect = [
            mock_scaling_group,  # scaling group exists check
            None,  # no existing agent
        ]
        mock_db_session.execute.return_value = None
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_db_session

        # When
        result = await db_source.upsert_agent_with_state(sample_heartbeat_upsert)

        # Then
        # For new agent: was_revived=False, need_resource_slot_update=True
        assert result.was_revived is False
        assert result.need_resource_slot_update is True
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_agent_with_state_existing_agent_alive(
        self,
        db_source: AgentDBSource,
        mock_db_engine: MagicMock,
        mock_db_session: AsyncMock,
        sample_heartbeat_upsert: AgentHeartbeatUpsert,
    ) -> None:
        # Given
        mock_scaling_group = MagicMock(spec=ScalingGroupRow)
        mock_agent_row = MagicMock(spec=AgentRow)
        mock_agent_data = AgentData(
            id=sample_heartbeat_upsert.metadata.id,
            status=AgentStatus.ALIVE,
            status_changed=datetime.now(tzutc()),
            region="us-west-1",
            scaling_group="default",
            available_slots=ResourceSlot({SlotName("cpu"): 8.0}),
            occupied_slots=ResourceSlot({}),
            addr="tcp://192.168.1.100:6001",
            architecture="x86_64",
            version="24.12.0",
            compute_plugins=[],
            first_contact=datetime.now(tzutc()),
            lost_at=None,
            public_host="192.168.1.100",
            public_key=PublicKey(b"test-public-key"),
            schedulable=True,
            auto_terminate_abusing_kernel=False,
        )
        mock_agent_row.to_data.return_value = mock_agent_data

        mock_db_session.scalar.side_effect = [
            mock_scaling_group,  # scaling group exists check
            mock_agent_row,  # existing agent found
        ]
        mock_db_session.execute.return_value = None
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_db_session

        # When
        result = await db_source.upsert_agent_with_state(sample_heartbeat_upsert)

        # Then
        assert result.was_revived is False
        assert result.need_resource_slot_update is True  # Changed to True: fields may differ
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_agent_with_state_revived_agent(
        self,
        db_source: AgentDBSource,
        mock_db_engine: MagicMock,
        mock_db_session: AsyncMock,
        sample_heartbeat_upsert: AgentHeartbeatUpsert,
    ) -> None:
        # Given
        mock_scaling_group = MagicMock(spec=ScalingGroupRow)
        mock_agent_row = MagicMock(spec=AgentRow)
        mock_agent_data = AgentData(
            id=sample_heartbeat_upsert.metadata.id,
            status=AgentStatus.LOST,  # Previously lost agent
            status_changed=datetime.now(tzutc()),
            region="us-west-1",
            scaling_group="default",
            available_slots=ResourceSlot({SlotName("cpu"): 8.0}),
            occupied_slots=ResourceSlot({}),
            addr="tcp://192.168.1.100:6001",
            architecture="x86_64",
            version="24.12.0",
            compute_plugins=[],
            first_contact=datetime.now(tzutc()),
            lost_at=datetime.now(tzutc()),
            public_host="192.168.1.100",
            public_key=PublicKey(b"test-public-key"),
            schedulable=True,
            auto_terminate_abusing_kernel=False,
        )
        mock_agent_row.to_data.return_value = mock_agent_data

        mock_db_session.scalar.side_effect = [
            mock_scaling_group,  # scaling group exists check
            mock_agent_row,  # existing lost agent found
        ]
        mock_db_session.execute.return_value = None
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_db_session

        # When
        result = await db_source.upsert_agent_with_state(sample_heartbeat_upsert)

        # Then
        assert result.was_revived is True  # Agent was revived from LOST state
        assert result.need_resource_slot_update is True  # Changed to True: fields may differ
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_agent_with_state_scaling_group_not_found(
        self,
        db_source: AgentDBSource,
        mock_db_engine: MagicMock,
        mock_db_session: AsyncMock,
        sample_heartbeat_upsert: AgentHeartbeatUpsert,
    ) -> None:
        # Given
        mock_db_session.scalar.return_value = None  # No scaling group found
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_db_session

        # When & Then
        with pytest.raises(ScalingGroupNotFound) as exc_info:
            await db_source.upsert_agent_with_state(sample_heartbeat_upsert)

        assert (
            str(exc_info.value)
            == f"No such scaling group. ({sample_heartbeat_upsert.metadata.scaling_group})"
        )
        mock_db_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_agent_with_new_resource_slots(
        self,
        db_source: AgentDBSource,
        mock_db_engine: MagicMock,
        mock_db_session: AsyncMock,
    ) -> None:
        # Given
        agent_id = AgentId("agent-002")
        agent_info = AgentInfo(
            ip="192.168.1.101",
            version="24.12.0",
            scaling_group="default",
            available_resource_slots=ResourceSlot({
                SlotName("cpu"): "8",
                SlotName("mem"): "32768",
                SlotName("cuda.shares"): "4",
                SlotName("rocm.device"): "2",  # New slot type
            }),
            slot_key_and_units={
                SlotName("cpu"): SlotTypes.COUNT,
                SlotName("mem"): SlotTypes.BYTES,
                SlotName("cuda.shares"): SlotTypes.COUNT,
                SlotName("rocm.device"): SlotTypes.COUNT,  # New slot type
            },
            compute_plugins={DeviceName("cpu"): {}},
            addr="tcp://192.168.1.101:6001",
            public_key=PublicKey(b"test-public-key-2"),
            public_host="192.168.1.101",
            images=b"\x82\xc4\x00\x00",
            region="us-east-1",
            architecture="x86_64",
            auto_terminate_abusing_kernel=False,
        )
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        mock_scaling_group = MagicMock(spec=ScalingGroupRow)
        mock_agent_row = MagicMock(spec=AgentRow)
        mock_agent_data = AgentData(
            id=agent_id,
            status=AgentStatus.ALIVE,
            status_changed=datetime.now(tzutc()),
            region="us-east-1",
            scaling_group="default",
            available_slots=ResourceSlot({
                SlotName("cpu"): 8.0,
                SlotName("mem"): 32768.0,
                SlotName("cuda.shares"): 4.0,
                # Note: no rocm.device slot
            }),
            occupied_slots=ResourceSlot({}),
            addr="tcp://192.168.1.101:6001",
            architecture="x86_64",
            version="24.12.0",
            compute_plugins=[],
            first_contact=datetime.now(tzutc()),
            lost_at=None,
            public_host="192.168.1.101",
            public_key=PublicKey(b"test-public-key"),
            schedulable=True,
            auto_terminate_abusing_kernel=False,
        )
        mock_agent_row.to_data.return_value = mock_agent_data

        mock_db_session.scalar.side_effect = [
            mock_scaling_group,  # scaling group exists check
            mock_agent_row,  # existing agent
        ]
        mock_db_session.execute.return_value = None
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_db_session

        # When
        result = await db_source.upsert_agent_with_state(upsert_data)

        # Then
        assert result.was_revived is False
        assert result.need_resource_slot_update is True  # New resource slot type detected
        mock_db_session.execute.assert_called_once()
