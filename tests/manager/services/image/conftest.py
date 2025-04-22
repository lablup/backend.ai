import pytest

from ai.backend.manager.server import agent_registry_ctx
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine):
    image_service = ImageService(db=database_engine, agent_registry=agent_registry_ctx)
    return ImageProcessors(image_service, [])
