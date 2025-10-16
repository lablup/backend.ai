from datetime import datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.types import AgentId, ImageID
from ai.backend.manager.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.manager.repositories.agent.cache_source.cache_source import AgentCacheSource


@pytest.fixture
def mock_valkey_image() -> AsyncMock:
    return AsyncMock(spec=ValkeyImageClient)


@pytest.fixture
def mock_valkey_live() -> AsyncMock:
    return AsyncMock(spec=ValkeyLiveClient)


@pytest.fixture
def cache_source(mock_valkey_image: AsyncMock, mock_valkey_live: AsyncMock) -> AgentCacheSource:
    return AgentCacheSource(valkey_image=mock_valkey_image, valkey_live=mock_valkey_live)


class TestAgentCacheSource:
    @pytest.mark.asyncio
    async def test_update_agent_last_seen_success(
        self,
        cache_source: AgentCacheSource,
        mock_valkey_live: AsyncMock,
    ) -> None:
        # Given
        agent_id = AgentId("agent-001")
        heartbeat_time = datetime.now(tzutc())

        # When
        await cache_source.update_agent_last_seen(agent_id, heartbeat_time)

        # Then
        mock_valkey_live.update_agent_last_seen.assert_called_once_with(
            agent_id, heartbeat_time.timestamp()
        )

    @pytest.mark.asyncio
    async def test_update_agent_last_seen_with_various_agent_ids(
        self,
        cache_source: AgentCacheSource,
        mock_valkey_live: AsyncMock,
    ) -> None:
        # Given
        test_cases = [
            AgentId("agent-simple"),
            AgentId("agent-with-dashes-123"),
            AgentId("agent.with.dots"),
            AgentId("123-numeric-agent"),
        ]
        heartbeat_time = datetime.now(tzutc())

        # When & Then
        for agent_id in test_cases:
            await cache_source.update_agent_last_seen(agent_id, heartbeat_time)
            mock_valkey_live.update_agent_last_seen.assert_called_with(
                agent_id, heartbeat_time.timestamp()
            )

    @pytest.mark.asyncio
    async def test_set_agent_to_images_success(
        self,
        cache_source: AgentCacheSource,
        mock_valkey_image: AsyncMock,
    ) -> None:
        # Given
        agent_id = AgentId("agent-001")
        image_ids = [
            ImageID(UUID("00000000-0000-0000-0000-000000000000")),
            ImageID(UUID("11111111-1111-1111-1111-111111111111")),
            ImageID(UUID("22222222-2222-2222-2222-222222222222")),
        ]

        # When
        await cache_source.set_agent_to_images(agent_id, image_ids)

        # Then
        mock_valkey_image.add_agent_to_images.assert_called_once_with(agent_id, image_ids)

    @pytest.mark.asyncio
    async def test_set_agent_to_images_empty_list(
        self,
        cache_source: AgentCacheSource,
        mock_valkey_image: AsyncMock,
    ) -> None:
        # Given
        agent_id = AgentId("agent-002")
        image_ids: list[ImageID] = []

        # When
        await cache_source.set_agent_to_images(agent_id, image_ids)

        # Then
        mock_valkey_image.add_agent_to_images.assert_called_once_with(agent_id, image_ids)

    @pytest.mark.asyncio
    async def test_set_agent_to_images_with_duplicates(
        self,
        cache_source: AgentCacheSource,
        mock_valkey_image: AsyncMock,
    ) -> None:
        # Given
        agent_id = AgentId("agent-003")
        images = [
            ImageID(UUID("00000000-0000-0000-0000-000000000000")),
            ImageID(UUID("00000000-0000-0000-0000-000000000000")),  # duplicate
            ImageID(UUID("11111111-1111-1111-1111-111111111111")),
        ]

        # When
        await cache_source.set_agent_to_images(agent_id, images)

        # Then
        mock_valkey_image.add_agent_to_images.assert_called_once_with(agent_id, images)

    @pytest.mark.asyncio
    async def test_cache_operations_with_concurrent_calls(
        self,
        cache_source: AgentCacheSource,
        mock_valkey_live: AsyncMock,
        mock_valkey_image: AsyncMock,
    ) -> None:
        # Given
        agents = [AgentId(f"agent-{i:03d}") for i in range(5)]
        heartbeat_time = datetime.now(tzutc())
        image_ids = [
            ImageID(UUID("00000000-0000-0000-0000-000000000000")),
            ImageID(UUID("11111111-1111-1111-1111-111111111111")),
        ]

        # When - simulate concurrent operations
        import asyncio

        tasks = []
        for agent_id in agents:
            tasks.append(cache_source.update_agent_last_seen(agent_id, heartbeat_time))
            tasks.append(cache_source.set_agent_to_images(agent_id, image_ids))

        await asyncio.gather(*tasks)

        # Then
        assert mock_valkey_live.update_agent_last_seen.call_count == 5
        assert mock_valkey_image.add_agent_to_images.call_count == 5

    @pytest.mark.asyncio
    async def test_cache_source_handles_valkey_errors_gracefully(
        self,
        cache_source: AgentCacheSource,
        mock_valkey_live: AsyncMock,
        mock_valkey_image: AsyncMock,
    ) -> None:
        # Given
        agent_id = AgentId("agent-error")
        heartbeat_time = datetime.now(tzutc())
        image_ids = [ImageID(UUID("22222222-2222-2222-2222-222222222222"))]

        # Configure mocks to raise exceptions
        mock_valkey_live.update_agent_last_seen.side_effect = ConnectionError(
            "Valkey connection lost"
        )
        mock_valkey_image.add_agent_to_images.side_effect = TimeoutError("Operation timed out")

        # When & Then - should not raise exceptions (handled in repository layer)
        with pytest.raises(ConnectionError):
            await cache_source.update_agent_last_seen(agent_id, heartbeat_time)

        with pytest.raises(TimeoutError):
            await cache_source.set_agent_to_images(agent_id, image_ids)
