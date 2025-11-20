from __future__ import annotations

import random
from typing import AsyncGenerator, cast

import pytest

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.data.image.types import InstalledImageInfo
from ai.backend.common.defs import REDIS_IMAGE_DB
from ai.backend.common.exception import ClientNotConnectedError
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import AgentId, ValkeyTarget


class TestValkeyImageClient:
    """Test cases for ValkeyImageClient"""

    @pytest.fixture
    async def valkey_image_client(
        self,
        redis_container,  # noqa: F811
    ) -> AsyncGenerator[ValkeyImageClient, None]:
        """Valkey client that auto-cleans installed image data after each test"""
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(
            addr=hostport_pair.address,
        )
        client = await ValkeyImageClient.create(
            valkey_target,
            human_readable_name="test.image",
            db_id=REDIS_IMAGE_DB,
        )
        try:
            yield client
        finally:
            # Cleanup all installed_image keys after test
            try:
                cursor = b"0"
                while cursor:
                    result = await client._client.client.scan(
                        cursor, match="installed_image:*", count=100
                    )
                    cursor = cast(bytes, result[0])
                    keys = cast(list[bytes], result[1])
                    if keys:
                        await client._client.client.delete(cast(list[str | bytes], keys))
                    if cursor == b"0":
                        break
            except ClientNotConnectedError:
                # Client already closed, skip cleanup
                pass
            await client.close()

    @pytest.mark.parametrize(
        ("installed_images", "expected_count"),
        [
            # Basic case: two images with same architecture
            (
                [
                    InstalledImageInfo(
                        canonical="cr.backend.ai/stable/python:3.11",
                        digest="sha256:abc123",
                        architecture="x86_64",
                    ),
                    InstalledImageInfo(
                        canonical="cr.backend.ai/stable/python:3.10",
                        digest="sha256:def456",
                        architecture="x86_64",
                    ),
                ],
                2,
            ),
            # Single image
            (
                [
                    InstalledImageInfo(
                        canonical="cr.backend.ai/stable/python:3.11",
                        digest="sha256:abc123",
                        architecture="x86_64",
                    ),
                ],
                1,
            ),
            # Same image with different architectures
            (
                [
                    InstalledImageInfo(
                        canonical="cr.backend.ai/stable/python:3.11",
                        digest="sha256:abc123",
                        architecture="x86_64",
                    ),
                    InstalledImageInfo(
                        canonical="cr.backend.ai/stable/python:3.11",
                        digest="sha256:def456",
                        architecture="aarch64",
                    ),
                ],
                2,
            ),
            # Empty list
            (
                [],
                0,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_add_and_get_agent_installed_images(
        self,
        valkey_image_client: ValkeyImageClient,
        installed_images: list[InstalledImageInfo],
        expected_count: int,
    ) -> None:
        """Test adding and retrieving installed images for an agent."""
        agent_id = AgentId(f"test-agent-{random.randint(1000, 9999)}")

        # Add installed images
        await valkey_image_client.add_agent_installed_images(agent_id, installed_images)

        # Retrieve installed images
        result = await valkey_image_client.get_agent_installed_images(agent_id)

        assert len(result) == expected_count
        for idx, expected_image in enumerate(installed_images):
            assert result[idx].canonical == expected_image.canonical
            assert result[idx].digest == expected_image.digest
            assert result[idx].architecture == expected_image.architecture

    @pytest.mark.asyncio
    async def test_get_agent_installed_images_nonexistent(
        self,
        valkey_image_client: ValkeyImageClient,
    ) -> None:
        """Test retrieving installed images for a nonexistent agent."""
        agent_id = AgentId(f"nonexistent-agent-{random.randint(1000, 9999)}")

        result = await valkey_image_client.get_agent_installed_images(agent_id)

        assert result == []

    @pytest.mark.asyncio
    async def test_add_agent_installed_images_overwrite(
        self,
        valkey_image_client: ValkeyImageClient,
    ) -> None:
        """Test that adding installed images overwrites previous data."""
        agent_id = AgentId(f"test-agent-{random.randint(1000, 9999)}")
        initial_images = [
            InstalledImageInfo(
                canonical="cr.backend.ai/stable/python:3.11",
                digest="sha256:abc123",
                architecture="x86_64",
            ),
        ]
        updated_images = [
            InstalledImageInfo(
                canonical="cr.backend.ai/stable/python:3.10",
                digest="sha256:def456",
                architecture="aarch64",
            ),
            InstalledImageInfo(
                canonical="cr.backend.ai/stable/python:3.9",
                digest="sha256:ghi789",
                architecture="aarch64",
            ),
        ]

        # Add initial images
        await valkey_image_client.add_agent_installed_images(agent_id, initial_images)

        # Add updated images (should overwrite)
        await valkey_image_client.add_agent_installed_images(agent_id, updated_images)

        # Retrieve and verify overwrite
        result = await valkey_image_client.get_agent_installed_images(agent_id)

        assert len(result) == 2
        assert result[0].canonical == "cr.backend.ai/stable/python:3.10"
        assert result[0].architecture == "aarch64"
        assert result[1].canonical == "cr.backend.ai/stable/python:3.9"
        assert result[1].architecture == "aarch64"
