import pytest

from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine):
    repository = ContainerRegistryRepository(
        db=database_engine,
    )
    admin_repository = AdminContainerRegistryRepository(
        db=database_engine,
    )
    container_registry_service = ContainerRegistryService(
        db=database_engine,
        container_registry_repository=repository,
        admin_container_registry_repository=admin_repository,
    )
    return ContainerRegistryProcessors(container_registry_service, [])
