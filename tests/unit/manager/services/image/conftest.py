"""
Mock-based fixtures for ImageService unit tests.

Tests verify service layer business logic using mocked repositories.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.types import ImageCanonical, ImageID, SlotName
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
)
from ai.backend.manager.models.image import ImageStatus, ImageType
from ai.backend.manager.repositories.image.admin_repository import AdminImageRepository
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService

if TYPE_CHECKING:
    pass


RESOURCE_LIMITS: dict[SlotName, dict[str, str | None]] = {
    SlotName("cuda.device"): {"min": "1", "max": None}
}


@pytest.fixture
def mock_image_repository() -> MagicMock:
    """Mock ImageRepository for testing."""
    return MagicMock(spec=ImageRepository)


@pytest.fixture
def mock_admin_image_repository() -> MagicMock:
    """Mock AdminImageRepository for testing."""
    return MagicMock(spec=AdminImageRepository)


@pytest.fixture
def mock_agent_registry() -> MagicMock:
    """Mock AgentRegistry for testing."""
    return MagicMock(spec="AgentRegistry")


@pytest.fixture
def image_service(
    mock_image_repository: MagicMock,
    mock_admin_image_repository: MagicMock,
    mock_agent_registry: MagicMock,
) -> ImageService:
    """Create ImageService with mock dependencies."""
    return ImageService(
        agent_registry=mock_agent_registry,
        image_repository=mock_image_repository,
        admin_image_repository=mock_admin_image_repository,
    )


@pytest.fixture
def processors(image_service: ImageService) -> ImageProcessors:
    """Create ImageProcessors with mock ImageService."""
    return ImageProcessors(image_service, [])


# Fixture data
@pytest.fixture
def container_registry_id() -> uuid.UUID:
    """Container registry ID for test fixtures."""
    return uuid.uuid4()


@pytest.fixture
def image_id() -> uuid.UUID:
    """Image ID for test fixtures."""
    return uuid.uuid4()


@pytest.fixture
def container_registry_data(container_registry_id: uuid.UUID) -> ContainerRegistryData:
    """Sample container registry data."""
    return ContainerRegistryData(
        id=container_registry_id,
        url="https://registry.example.com",
        registry_name="registry.example.com",
        type=ContainerRegistryType.DOCKER,
        project="test_project",
        username=None,
        password=None,
        ssl_verify=True,
        is_global=True,
        extra=None,
    )


@pytest.fixture
def image_data(image_id: uuid.UUID, container_registry_id: uuid.UUID) -> ImageData:
    """Sample image data for testing."""
    return ImageData(
        id=ImageID(image_id),
        name=ImageCanonical("registry.example.com/test_project/python:3.9-ubuntu20.04"),
        image="test_project/python",
        project="test_project",
        tag="3.9-ubuntu20.04",
        registry="registry.example.com",
        registry_id=container_registry_id,
        architecture="x86_64",
        accelerators="cuda",
        config_digest="sha256:abcdefgh0123456789abcdefgh0123456789abcdefgh0123456789abcd".ljust(
            72, " "
        ),
        size_bytes=12345678,
        is_local=False,
        type=ImageType.COMPUTE,
        labels=ImageLabelsData(label_data={}),
        resources=ImageResourcesData(resources_data=RESOURCE_LIMITS),
        status=ImageStatus.ALIVE,
        created_at=datetime(2023, 9, 30, 15, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def image_alias_id() -> uuid.UUID:
    """Image alias ID for test fixtures."""
    return uuid.uuid4()


@pytest.fixture
def image_alias_data(image_alias_id: uuid.UUID) -> ImageAliasData:
    """Sample image alias data for testing."""
    return ImageAliasData(
        id=image_alias_id,
        alias="python",
    )
