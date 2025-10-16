import zlib
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from dateutil.tz import tzutc

from ai.backend.common import msgpack
from ai.backend.common.auth import PublicKey
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.types import AgentId, DeviceName, ResourceSlot, SlotName, SlotTypes
from ai.backend.manager.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import (
    AgentData,
    AgentHeartbeatUpsert,
    AgentStatus,
    UpsertResult,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.cache_source.cache_source import AgentCacheSource
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.repositories.agent.repository import AgentRepository


@pytest.fixture
def mock_db_engine() -> MagicMock:
    return MagicMock(spec=ExtendedAsyncSAEngine)


@pytest.fixture
def mock_valkey_image() -> AsyncMock:
    return AsyncMock(spec=ValkeyImageClient)


@pytest.fixture
def mock_valkey_live() -> AsyncMock:
    return AsyncMock(spec=ValkeyLiveClient)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    mock = MagicMock(spec=ManagerConfigProvider)
    mock.legacy_etcd_config_loader = AsyncMock()
    mock.legacy_etcd_config_loader.update_resource_slots = AsyncMock()
    return mock


@pytest.fixture
def mock_db_source() -> AsyncMock:
    return AsyncMock(spec=AgentDBSource)


@pytest.fixture
def mock_cache_source() -> AsyncMock:
    return AsyncMock(spec=AgentCacheSource)


@pytest.fixture
def agent_repository(
    mock_db_engine: MagicMock,
    mock_valkey_image: AsyncMock,
    mock_valkey_live: AsyncMock,
    mock_config_provider: MagicMock,
) -> AgentRepository:
    return AgentRepository(
        db=mock_db_engine,
        valkey_image=mock_valkey_image,
        valkey_live=mock_valkey_live,
        config_provider=mock_config_provider,
    )


@pytest.fixture
def sample_agent_info() -> AgentInfo:
    return AgentInfo(
        ip="192.168.1.100",
        version="24.12.0",
        scaling_group="default",
        available_resource_slots=ResourceSlot({
            SlotName("cpu"): "8",
            SlotName("mem"): "32768",
        }),
        slot_key_and_units={
            SlotName("cpu"): SlotTypes.COUNT,
            SlotName("mem"): SlotTypes.BYTES,
        },
        addr="tcp://192.168.1.100:6001",
        public_key=PublicKey(b"test-public-key"),
        public_host="192.168.1.100",
        images=b"\x82\xc4\x00\x00",  # msgpack compressed data
        region="us-west-1",
        architecture="x86_64",
        compute_plugins={DeviceName("cpu"): {}},
        auto_terminate_abusing_kernel=False,
    )


class TestAgentRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_delegates_to_db_source(
        self,
        agent_repository: AgentRepository,
    ) -> None:
        # Given
        agent_id = AgentId("agent-001")
        expected_data = AgentData(
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

        # Patch the db_source directly
        with patch.object(
            agent_repository._db_source, "get_by_id", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = expected_data

            # When
            result = await agent_repository.get_by_id(agent_id)

            # Then
            assert result == expected_data
            mock_get.assert_called_once_with(agent_id)

    @pytest.mark.asyncio
    async def test_add_agent_to_images_processes_compressed_data(
        self,
        agent_repository: AgentRepository,
    ) -> None:
        # Given
        agent_id = AgentId("agent-001")
        images = [
            (
                "python:3.11-slim",
                {
                    "canonical": "python:3.11-slim",
                    "digest": "sha256:abc123",
                },
            ),
            (
                "tensorflow/tensorflow:latest",
                {
                    "canonical": "tensorflow/tensorflow:latest",
                    "digest": "sha256:def456",
                },
            ),
            (
                "pytorch/pytorch:2.0-cuda",
                {
                    "canonical": "pytorch/pytorch:2.0-cuda",
                    "digest": "sha256:ghi789",
                },
            ),
        ]
        image_ids = [
            UUID("00000000-0000-0000-0000-000000000000"),
            UUID("11111111-1111-1111-1111-111111111111"),
            UUID("22222222-2222-2222-2222-222222222222"),
        ]
        compressed_images = zlib.compress(msgpack.packb(images))

        # Patch the cache_source directly
        with (
            patch.object(
                agent_repository._cache_source, "set_agent_to_images", new_callable=AsyncMock
            ) as mock_set,
            patch.object(
                agent_repository._db_source, "get_images_by_digest", new_callable=AsyncMock
            ) as mock_get_images,
        ):
            mock_get_images.return_value = {image_id: None for image_id in image_ids}
            # When
            await agent_repository.add_agent_to_images(agent_id, compressed_images)

            # Then
            mock_set.assert_called_once()
            call_args = mock_set.call_args[0]
            assert call_args[0] == agent_id
            assert set(call_args[1]) == {
                UUID("00000000-0000-0000-0000-000000000000"),
                UUID("11111111-1111-1111-1111-111111111111"),
                UUID("22222222-2222-2222-2222-222222222222"),
            }

    @pytest.mark.asyncio
    async def test_add_agent_to_images_handles_errors_gracefully(
        self,
        agent_repository: AgentRepository,
    ) -> None:
        # Given
        agent_id = AgentId("agent-error")
        images = [
            (
                "broken:image",
                {"canonical": "broken:image", "digest": "sha256:broken"},
            )
        ]
        image_ids = [UUID("33333333-3333-3333-3333-333333333333")]
        compressed_images = zlib.compress(msgpack.packb(images))

        # Patch the cache_source to raise an exception
        with (
            patch.object(
                agent_repository._cache_source, "set_agent_to_images", new_callable=AsyncMock
            ) as mock_set,
            patch.object(
                agent_repository._db_source, "get_images_by_digest", new_callable=AsyncMock
            ) as mock_get_images,
        ):
            mock_set.side_effect = Exception("Cache error")
            mock_get_images.return_value = {image_id: None for image_id in image_ids}

            # When - should not raise exception (suppressed with log)
            await agent_repository.add_agent_to_images(agent_id, compressed_images)

            # Then
            mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_agent_heartbeat_normal_update(
        self,
        agent_repository: AgentRepository,
        mock_config_provider: MagicMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        # Given
        agent_id = AgentId("agent-001")
        heartbeat_time = datetime.now(tzutc())
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=heartbeat_time,
        )

        expected_upsert_result = UpsertResult(
            was_revived=False,
            need_resource_slot_update=False,
        )

        # Patch both cache_source and db_source
        with (
            patch.object(
                agent_repository._cache_source, "update_agent_last_seen", new_callable=AsyncMock
            ) as mock_update_last_seen,
            patch.object(
                agent_repository._db_source, "upsert_agent_with_state", new_callable=AsyncMock
            ) as mock_upsert,
        ):
            mock_upsert.return_value = expected_upsert_result

            # When
            result = await agent_repository.sync_agent_heartbeat(agent_id, upsert_data)

            # Then
            assert result == expected_upsert_result
            mock_update_last_seen.assert_called_once_with(agent_id, heartbeat_time)
            mock_upsert.assert_called_once_with(upsert_data)
            mock_config_provider.legacy_etcd_config_loader.update_resource_slots.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_agent_heartbeat_with_resource_slot_update(
        self,
        agent_repository: AgentRepository,
        mock_config_provider: MagicMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        # Given
        agent_id = AgentId("agent-002")
        heartbeat_time = datetime.now(tzutc())
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=heartbeat_time,
        )

        expected_upsert_result = UpsertResult(
            was_revived=False,
            need_resource_slot_update=True,  # Needs update
        )

        with (
            patch.object(
                agent_repository._cache_source, "update_agent_last_seen", new_callable=AsyncMock
            ) as mock_update_last_seen,
            patch.object(
                agent_repository._db_source, "upsert_agent_with_state", new_callable=AsyncMock
            ) as mock_upsert,
        ):
            mock_upsert.return_value = expected_upsert_result

            # When
            result = await agent_repository.sync_agent_heartbeat(agent_id, upsert_data)

            # Then
            assert result == expected_upsert_result
            mock_update_last_seen.assert_called_once_with(agent_id, heartbeat_time)
            mock_upsert.assert_called_once_with(upsert_data)
            # Should update resource slots in etcd
            mock_config_provider.legacy_etcd_config_loader.update_resource_slots.assert_called_once_with(
                upsert_data.resource_info.slot_key_and_units
            )

    @pytest.mark.asyncio
    async def test_sync_agent_heartbeat_cache_error_does_not_fail(
        self,
        agent_repository: AgentRepository,
        mock_config_provider: MagicMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        # Given
        agent_id = AgentId("agent-003")
        heartbeat_time = datetime.now(tzutc())
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=heartbeat_time,
        )

        expected_upsert_result = UpsertResult(
            was_revived=False,
            need_resource_slot_update=False,
        )

        with (
            patch.object(
                agent_repository._cache_source, "update_agent_last_seen", new_callable=AsyncMock
            ) as mock_update_last_seen,
            patch.object(
                agent_repository._db_source, "upsert_agent_with_state", new_callable=AsyncMock
            ) as mock_upsert,
        ):
            mock_update_last_seen.side_effect = Exception("Cache connection error")
            mock_upsert.return_value = expected_upsert_result

            # When - should not fail despite cache error
            result = await agent_repository.sync_agent_heartbeat(agent_id, upsert_data)

            # Then
            assert result == expected_upsert_result
            mock_update_last_seen.assert_called_once_with(agent_id, heartbeat_time)
            mock_upsert.assert_called_once_with(upsert_data)

    @pytest.mark.asyncio
    async def test_sync_agent_heartbeat_revival_scenario(
        self,
        agent_repository: AgentRepository,
        mock_config_provider: MagicMock,
        sample_agent_info: AgentInfo,
    ) -> None:
        # Given
        agent_id = AgentId("agent-revival")
        heartbeat_time = datetime.now(tzutc())
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=sample_agent_info,
            heartbeat_received=heartbeat_time,
        )

        expected_upsert_result = UpsertResult(
            was_revived=True,  # Agent was revived
            need_resource_slot_update=False,
        )

        with (
            patch.object(
                agent_repository._cache_source, "update_agent_last_seen", new_callable=AsyncMock
            ) as mock_update_last_seen,
            patch.object(
                agent_repository._db_source, "upsert_agent_with_state", new_callable=AsyncMock
            ) as mock_upsert,
        ):
            mock_upsert.return_value = expected_upsert_result

            # When
            result = await agent_repository.sync_agent_heartbeat(agent_id, upsert_data)

            # Then
            assert result == expected_upsert_result
            assert result.was_revived is True
            mock_update_last_seen.assert_called_once_with(agent_id, heartbeat_time)
            mock_upsert.assert_called_once_with(upsert_data)
