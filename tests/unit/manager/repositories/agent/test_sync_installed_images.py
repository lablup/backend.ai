from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.image.types import InstalledImageInfo
from ai.backend.common.types import AgentId, ImageID, ValkeyTarget
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.testutils.db import with_tables


@dataclass
class _TestImageInput:
    """Input data for creating a test image."""

    name: str
    architecture: str
    digest: str


@dataclass
class _TestImageData:
    """Test data for a single image."""

    id: str
    name: str
    architecture: str


class TestSyncInstalledImagesIntegration:
    """Integration test suite for sync_installed_images functionality using real DB."""

    @pytest.fixture
    async def valkey_image_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyImageClient, None]:
        """Create ValkeyImageClient with real Redis container."""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyImageClient.create(
            valkey_target=valkey_target,
            db_id=1,
            human_readable_name="test-valkey-image",
        )

        try:
            await client._client.client.flushdb()
            yield client
        finally:
            await client.close()

    @pytest.fixture
    async def valkey_live_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyLiveClient, None]:
        """Create ValkeyLiveClient with real Redis container."""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyLiveClient.create(
            valkey_target=valkey_target,
            db_id=2,
            human_readable_name="test-valkey-live",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    async def valkey_stat_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyStatClient, None]:
        """Create ValkeyStatClient with real Redis container."""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyStatClient.create(
            valkey_target=valkey_target,
            db_id=3,
            human_readable_name="test-valkey-stat",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    async def config_provider(
        self,
    ) -> ManagerConfigProvider:
        """Create config provider with etcd context."""
        mock = MagicMock(spec=ManagerConfigProvider)
        mock.legacy_etcd_config_loader = AsyncMock()
        mock.legacy_etcd_config_loader.update_resource_slots = AsyncMock()
        return mock

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                ContainerRegistryRow,
                ImageRow,
                ImageAliasRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def agent_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        valkey_image_client: ValkeyImageClient,
        valkey_live_client: ValkeyLiveClient,
        valkey_stat_client: ValkeyStatClient,
        config_provider: ManagerConfigProvider,
    ) -> AgentRepository:
        """Create AgentRepository with all dependencies."""
        return AgentRepository(
            db=db_with_cleanup,
            valkey_image=valkey_image_client,
            valkey_live=valkey_live_client,
            valkey_stat=valkey_stat_client,
            config_provider=config_provider,
        )

    @asynccontextmanager
    async def create_test_images(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        images_data: list[_TestImageInput],
    ) -> AsyncIterator[list[_TestImageData]]:
        """Create test images in DB. TRUNCATE CASCADE handles cleanup."""
        test_images: list[_TestImageData] = []
        registry_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_session:
            # Create container registry first
            registry = ContainerRegistryRow(
                id=registry_id,
                url="https://cr.backend.ai",
                registry_name="test-registry",
                type=ContainerRegistryType.HARBOR2,
                project="stable",
                username="test",
                password="test",
            )
            db_session.add(registry)
            await db_session.flush()

            # Create images
            for img_data in images_data:
                image = ImageRow(
                    name=img_data.name,
                    project="stable",
                    registry=str(registry_id),
                    registry_id=registry_id,
                    image=img_data.name.split("/")[-1],
                    tag="latest",
                    architecture=img_data.architecture,
                    config_digest=img_data.digest,
                    size_bytes=1000000,
                    type=ImageType.COMPUTE,
                    accelerators=None,
                    resources={},
                    labels={},
                )
                db_session.add(image)
                await db_session.flush()
                test_images.append(
                    _TestImageData(
                        id=str(image.id),
                        name=img_data.name,
                        architecture=img_data.architecture,
                    )
                )

            await db_session.commit()

        yield test_images

    @pytest.mark.asyncio
    async def test_sync_installed_images_with_digest_mismatch(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        valkey_image_client: ValkeyImageClient,
        agent_repository: AgentRepository,
    ) -> None:
        """
        Verify that sync works when agent digest differs from DB digest.
        """
        async with self.create_test_images(
            db_with_cleanup,
            [
                _TestImageInput(
                    name="cr.backend.ai/stable/python:3.11-ubuntu20.04",
                    architecture="x86_64",
                    digest="sha256:db_digest_001",
                ),
                _TestImageInput(
                    name="cr.backend.ai/stable/pytorch:2.0-py311",
                    architecture="x86_64",
                    digest="sha256:db_digest_002",
                ),
            ],
        ) as test_images:
            # Given: Agent reports installed images with different digests than DB
            agent_id = AgentId("test-agent-001")

            # Agent reports these images with different digests
            installed_images = [
                InstalledImageInfo(
                    canonical="cr.backend.ai/stable/python:3.11-ubuntu20.04",
                    digest="sha256:changed_digest_by_image_driver_001",  # different digest from DB
                    architecture="x86_64",
                ),
                InstalledImageInfo(
                    canonical="cr.backend.ai/stable/pytorch:2.0-py311",
                    digest="sha256:changed_digest_by_image_driver_002",  # different digest from DB
                    architecture="x86_64",
                ),
            ]

            # Store in Redis (simulating agent's heartbeat)
            images_json = json.dumps([img.model_dump() for img in installed_images])
            await valkey_image_client._client.client.set(
                key=f"installed_image:{agent_id}",
                value=images_json,
            )

            # When: sync_installed_images is called
            await agent_repository.sync_installed_images(agent_id)

            # Then: Images should be found and cached despite digest mismatch
            cached_agents_001 = await valkey_image_client.get_agents_for_image(
                ImageID(uuid.UUID(test_images[0].id))
            )
            cached_agents_002 = await valkey_image_client.get_agents_for_image(
                ImageID(uuid.UUID(test_images[1].id))
            )

            assert agent_id in cached_agents_001, "First image should be cached"
            assert agent_id in cached_agents_002, "Second image should be cached"

    @pytest.mark.asyncio
    async def test_sync_installed_images_empty_redis(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        valkey_image_client: ValkeyImageClient,
        agent_repository: AgentRepository,
    ) -> None:
        """Test sync when Redis has no installed images for the agent."""
        async with self.create_test_images(
            db_with_cleanup,
            [
                _TestImageInput(
                    name="cr.backend.ai/stable/python:3.11-ubuntu20.04",
                    architecture="x86_64",
                    digest="sha256:db_digest_001",
                ),
            ],
        ) as test_images:
            # Given: No installed images in Redis
            agent_id = AgentId("test-agent-empty")

            # When: sync_installed_images is called
            await agent_repository.sync_installed_images(agent_id)

            # Then: Should complete without error, no images cached
            # Verify agent is not associated with any images
            for test_image in test_images:
                cached_agents = await valkey_image_client.get_agents_for_image(
                    ImageID(uuid.UUID(test_image.id))
                )
                assert agent_id not in cached_agents

    @pytest.mark.asyncio
    async def test_sync_installed_images_multiple_architectures(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        valkey_image_client: ValkeyImageClient,
        agent_repository: AgentRepository,
    ) -> None:
        """Test sync with same image name but different architectures."""
        async with self.create_test_images(
            db_with_cleanup,
            [
                _TestImageInput(
                    name="cr.backend.ai/stable/python:3.11",
                    architecture="x86_64",
                    digest="sha256:db_digest_x86",
                ),
                _TestImageInput(
                    name="cr.backend.ai/stable/python:3.11",
                    architecture="aarch64",
                    digest="sha256:db_digest_arm",
                ),
            ],
        ) as test_images:
            # Given: Agent has same image with different architectures
            agent_id = AgentId("test-agent-multi-arch")

            installed_images = [
                InstalledImageInfo(
                    canonical="cr.backend.ai/stable/python:3.11",
                    digest="sha256:agent_x86_digest",
                    architecture="x86_64",
                ),
                InstalledImageInfo(
                    canonical="cr.backend.ai/stable/python:3.11",
                    digest="sha256:agent_arm_digest",
                    architecture="aarch64",
                ),
            ]

            images_json = json.dumps([img.model_dump() for img in installed_images])
            await valkey_image_client._client.client.set(
                key=f"installed_image:{agent_id}",
                value=images_json,
            )

            # When: sync_installed_images is called
            await agent_repository.sync_installed_images(agent_id)

            # Then: Both architectures should be cached
            x86_image = test_images[0]  # cr.backend.ai/stable/python:3.11 x86_64
            arm_image = test_images[1]  # cr.backend.ai/stable/python:3.11 aarch64

            cached_x86 = await valkey_image_client.get_agents_for_image(
                ImageID(uuid.UUID(x86_image.id))
            )
            cached_arm = await valkey_image_client.get_agents_for_image(
                ImageID(uuid.UUID(arm_image.id))
            )

            assert agent_id in cached_x86, "x86_64 image should be cached"
            assert agent_id in cached_arm, "aarch64 image should be cached"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "architecture",
        ["x86_64", "aarch64"],
    )
    async def test_sync_installed_images_different_architectures(
        self,
        architecture: str,
        db_with_cleanup: ExtendedAsyncSAEngine,
        valkey_image_client: ValkeyImageClient,
        agent_repository: AgentRepository,
    ) -> None:
        """Test sync works correctly for x86_64 and aarch64 separately."""
        async with self.create_test_images(
            db_with_cleanup,
            [
                _TestImageInput(
                    name="cr.backend.ai/stable/python:3.11",
                    architecture=architecture,
                    digest=f"sha256:db_digest_{architecture}",
                ),
            ],
        ) as test_images:
            # Given: Agent with specific architecture image
            agent_id = AgentId(f"test-agent-{architecture}")

            installed_images = [
                InstalledImageInfo(
                    canonical="cr.backend.ai/stable/python:3.11",
                    digest=f"sha256:agent_{architecture}_digest",
                    architecture=architecture,
                ),
            ]

            images_json = json.dumps([img.model_dump() for img in installed_images])
            await valkey_image_client._client.client.set(
                key=f"installed_image:{agent_id}",
                value=images_json,
            )

            # When: sync_installed_images is called
            await agent_repository.sync_installed_images(agent_id)

            # Then: Image with correct architecture should be cached
            test_image = test_images[0]
            cached_agents = await valkey_image_client.get_agents_for_image(
                ImageID(uuid.UUID(test_image.id))
            )
            assert agent_id in cached_agents, f"{architecture} image should be cached"

    @pytest.mark.asyncio
    async def test_sync_installed_images_partial_match(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        valkey_image_client: ValkeyImageClient,
        agent_repository: AgentRepository,
    ) -> None:
        """Test when some agent-reported images don't exist in DB."""
        async with self.create_test_images(
            db_with_cleanup,
            [
                _TestImageInput(
                    name="cr.backend.ai/stable/python:3.11-ubuntu20.04",
                    architecture="x86_64",
                    digest="sha256:db_digest_001",
                ),
                _TestImageInput(
                    name="cr.backend.ai/stable/pytorch:2.0-py311",
                    architecture="x86_64",
                    digest="sha256:db_digest_002",
                ),
            ],
        ) as test_images:
            # Given: Agent reports 3 images, but only 2 exist in DB
            agent_id = AgentId("test-agent-partial")

            installed_images = [
                InstalledImageInfo(
                    canonical="cr.backend.ai/stable/python:3.11-ubuntu20.04",
                    digest="sha256:digest_001",
                    architecture="x86_64",
                ),
                InstalledImageInfo(
                    canonical="cr.backend.ai/stable/nonexistent:latest",  # Doesn't exist in DB
                    digest="sha256:digest_002",
                    architecture="x86_64",
                ),
                InstalledImageInfo(
                    canonical="cr.backend.ai/stable/pytorch:2.0-py311",
                    digest="sha256:digest_003",
                    architecture="x86_64",
                ),
            ]

            images_json = json.dumps([img.model_dump() for img in installed_images])
            await valkey_image_client._client.client.set(
                key=f"installed_image:{agent_id}",
                value=images_json,
            )

            # When: sync_installed_images is called
            await agent_repository.sync_installed_images(agent_id)

            # Then: Only existing images should be cached (2 out of 3)
            cached_001 = await valkey_image_client.get_agents_for_image(
                ImageID(uuid.UUID(test_images[0].id))
            )
            cached_002 = await valkey_image_client.get_agents_for_image(
                ImageID(uuid.UUID(test_images[1].id))
            )

            assert agent_id in cached_001, "First existing image should be cached"
            assert agent_id in cached_002, "Second existing image should be cached"
