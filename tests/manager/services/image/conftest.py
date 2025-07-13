import pytest

from ai.backend.manager.repositories.image.admin_repository import AdminImageRepository
from ai.backend.manager.repositories.image.repository import ImageRepository
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine, registry_ctx):
    agent_registry, _, _, _, _, _, _ = registry_ctx
    image_repository = ImageRepository(database_engine)
    admin_repository = AdminImageRepository(database_engine)
    image_service = ImageService(
        agent_registry=agent_registry,
        image_repository=image_repository,
        admin_image_repository=admin_repository,
    )
    return ImageProcessors(image_service, [])
