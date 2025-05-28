import pytest

from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine, registry_ctx):
    agent_registry, _, _, _, _, _, _ = registry_ctx
    image_service = ImageService(db=database_engine, agent_registry=agent_registry)
    return ImageProcessors(image_service, [])
