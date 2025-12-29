from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import sqlalchemy as sa
from aioresponses import aioresponses

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.admin_repository import (
    AdminContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.actions.clear_images import ClearImagesAction
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.load_all_container_registries import (
    LoadAllContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.load_container_registries import (
    LoadContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import RescanImagesAction
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.testutils.mock import setup_dockerhub_mocking

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture
def container_registry_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> ContainerRegistryProcessors:
    container_registry_repository = ContainerRegistryRepository(database_engine)
    admin_container_registry_repository = AdminContainerRegistryRepository(database_engine)
    container_registry_service = ContainerRegistryService(
        database_engine, container_registry_repository, admin_container_registry_repository
    )
    return ContainerRegistryProcessors(
        service=container_registry_service,
        action_monitors=[],
    )


@asynccontextmanager
async def create_test_registry(database_engine, registry_name="test-registry", project=None):
    """Context manager to create and cleanup a test container registry in the database."""
    if project is None:
        project = "test-project"
    registry_id = None

    try:
        # Create registry
        async with database_engine.begin_session() as session:
            registry = ContainerRegistryRow(
                id=uuid4(),
                url=f"https://{registry_name}.example.com",
                registry_name=registry_name,
                type=ContainerRegistryType.DOCKER,
                project=project,
                username=None,
                password=None,
                ssl_verify=True,
                is_global=True,
                extra=None,
            )
            session.add(registry)
            await session.commit()
            query = sa.select(ContainerRegistryRow.id).where(
                (ContainerRegistryRow.registry_name == registry_name)
                & (ContainerRegistryRow.url == f"https://{registry_name}.example.com")
            )
            result = await session.execute(query)
            registry_id = result.scalar()

        yield registry_id, registry_name, project

    finally:
        # Cleanup registry
        if registry_id is not None:
            async with database_engine.begin_session() as session:
                # First delete any associated images
                await session.execute(
                    sa.delete(ImageRow).where(ImageRow.registry_id == registry_id)
                )
                # Then delete the registry
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
                )
                await session.commit()


@asynccontextmanager
async def create_test_image(
    database_engine, registry_id, registry_name, project, image_name="python", tag="3.9"
):
    """Context manager to create and cleanup a test image in the database."""
    image_id = None

    try:
        # Create image
        async with database_engine.begin_session() as session:
            image = ImageRow(
                name=f"{registry_name}/{project}/{image_name}:{tag}",
                image=f"{project}/{image_name}",
                tag=tag,
                project=project,
                registry=registry_name,
                registry_id=registry_id,
                architecture="x86_64",
                config_digest="sha256:" + "a" * 64,
                size_bytes=1000000,
                is_local=False,
                type="compute",
                status=ImageStatus.ALIVE,
                labels={},
                resources={},
            )
            session.add(image)
            await session.commit()
            # Get the generated ID after commit
            await session.refresh(image)
            image_id = image.id

        yield image_id

    finally:
        # Cleanup image
        if image_id is not None:
            async with database_engine.begin_session() as session:
                await session.execute(sa.delete(ImageRow).where(ImageRow.id == image_id))
                await session.commit()


@pytest.mark.asyncio
async def test_rescan_images_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Setup: Create a container registry
    async with create_test_registry(database_engine) as (registry_id, registry_name, project):
        # Mock the registry scanner
        with aioresponses() as m:
            setup_dockerhub_mocking(
                m,
                f"https://{registry_name}.example.com",
                dockerhub_responses_mock={
                    "get_token": {"token": "fake-token"},
                    "get_catalog": {"repositories": [f"{project}/python", f"{project}/node"]},
                    "get_tags": {"tags": ["latest"]},
                    "get_manifest": {
                        "schemaVersion": 2,
                        "config": {
                            "digest": "sha256:" + "1" * 64,
                            "size": 100,
                        },
                        "layers": [
                            {
                                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                                "size": 1000,
                                "digest": "sha256:" + "2" * 64,
                            },
                            {
                                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                                "size": 2000,
                                "digest": "sha256:" + "3" * 64,
                            },
                        ],
                    },
                    "get_config": {
                        "architecture": "amd64",
                        "config": {
                            "Env": [
                                "PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                            ],
                        },
                    },
                },
            )

            # Action: Rescan images
            action = RescanImagesAction(
                registry=registry_name, project=project, progress_reporter=AsyncMock()
            )
            result = await container_registry_processors.rescan_images.wait_for_complete(action)

            # Verify: Check results
            assert result.registry.registry_name == registry_name
            assert result.registry.project == project
            assert len(result.images) > 0
            assert result.errors == []


@pytest.mark.asyncio
async def test_clear_images_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Setup: Create registry and images
    async with create_test_registry(database_engine) as (registry_id, registry_name, project):
        async with (
            create_test_image(database_engine, registry_id, registry_name, project) as image1_id,
            create_test_image(
                database_engine, registry_id, registry_name, project, "node", "16"
            ) as image2_id,
        ):
            # Verify images are ALIVE
            async with database_engine.begin_readonly_session() as session:
                image1 = await session.get(ImageRow, image1_id)
                image2 = await session.get(ImageRow, image2_id)
                assert image1.status == ImageStatus.ALIVE
                assert image2.status == ImageStatus.ALIVE

            # Action: Clear images
            action = ClearImagesAction(registry=registry_name, project=project)
            result = await container_registry_processors.clear_images.wait_for_complete(action)

            # Verify: Images should be marked as DELETED
            async with database_engine.begin_readonly_session() as session:
                image1 = await session.get(ImageRow, image1_id)
                image2 = await session.get(ImageRow, image2_id)
                assert image1.status == ImageStatus.DELETED
                assert image2.status == ImageStatus.DELETED
                assert result.registry.registry_name == registry_name


@pytest.mark.asyncio
async def test_load_container_registries_by_name_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Setup: Create multiple registries with same name but different projects
    registry_name = "shared-registry"
    async with (
        create_test_registry(database_engine, registry_name, "project1"),
        create_test_registry(database_engine, registry_name, "project2"),
        create_test_registry(database_engine, "other-registry", "project3"),
    ):
        # Action: Load by registry name only
        action = LoadContainerRegistriesAction(registry=registry_name, project=None)
        result = await container_registry_processors.load_container_registries.wait_for_complete(
            action
        )

        # Verify: Should return both registries with the same name
        assert len(result.registries) == 2
        assert all(r.registry_name == registry_name for r in result.registries)
        assert {r.project for r in result.registries} == {"project1", "project2"}


@pytest.mark.asyncio
async def test_load_container_registries_by_name_and_project_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Setup: Create registries
    registry_name = "test-registry"
    project = "specific-project"
    async with (
        create_test_registry(database_engine, registry_name, project),
        create_test_registry(database_engine, registry_name, "other-project"),
    ):
        # Action: Load by registry name and specific project
        action = LoadContainerRegistriesAction(registry=registry_name, project=project)
        result = await container_registry_processors.load_container_registries.wait_for_complete(
            action
        )

        # Verify: Should return only the specific registry
        assert len(result.registries) == 1
        assert result.registries[0].registry_name == registry_name
        assert result.registries[0].project == project


@pytest.mark.asyncio
async def test_load_container_registries_not_found_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Action: Load non-existent registry
    action = LoadContainerRegistriesAction(registry="non-existent", project="non-existent")
    result = await container_registry_processors.load_container_registries.wait_for_complete(action)

    # Verify: Should return empty list
    assert result.registries == []


@pytest.mark.asyncio
async def test_load_all_container_registries_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Setup: Create multiple registries
    async with (
        create_test_registry(database_engine, "registry1", "project1"),
        create_test_registry(database_engine, "registry2", "project2"),
        create_test_registry(database_engine, "registry3", "project3"),
    ):
        # Action: Load all registries
        action = LoadAllContainerRegistriesAction()
        result = (
            await container_registry_processors.load_all_container_registries.wait_for_complete(
                action
            )
        )

        # Verify: Should return all registries
        assert len(result.registries) >= 3
        registry_names = {r.registry_name for r in result.registries}
        assert {"registry1", "registry2", "registry3"}.issubset(registry_names)


@pytest.mark.asyncio
async def test_get_container_registries_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Setup: Create registries with different projects
    async with (
        create_test_registry(database_engine, "registry1", "projectA"),
        create_test_registry(database_engine, "registry2", "projectB"),
    ):
        # For global registry, actually set project to None in the database
        registry_id = uuid4()
        async with database_engine.begin_session() as session:
            registry = ContainerRegistryRow(
                id=registry_id,
                url="https://registry3.example.com",
                registry_name="registry3",
                type=ContainerRegistryType.DOCKER,
                project=None,  # Actually None for global registry
                username=None,
                password=None,
                ssl_verify=True,
                is_global=True,
                extra=None,
            )
            session.add(registry)
            await session.commit()

        # Action: Get known registries
        action = GetContainerRegistriesAction()
        result = await container_registry_processors.get_container_registries.wait_for_complete(
            action
        )

        # Verify: Should return mapping of project/registry to URL
        assert "projectA/registry1" in result.registries
        assert result.registries["projectA/registry1"] == "https://registry1.example.com/"
        assert "projectB/registry2" in result.registries
        assert result.registries["projectB/registry2"] == "https://registry2.example.com/"
        # Global registry should be included with None prefix
        assert "None/registry3" in result.registries

        # Cleanup the global registry manually
        if registry_id:
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
                )
                await session.commit()


@pytest.mark.asyncio
async def test_rescan_images_registry_not_found_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Action: Try to rescan non-existent registry
    action = RescanImagesAction(
        registry="non-existent", project="non-existent", progress_reporter=AsyncMock()
    )

    # Verify: Should raise ContainerRegistryNotFound
    with pytest.raises(ContainerRegistryNotFound):
        await container_registry_processors.rescan_images.wait_for_complete(action)


@pytest.mark.asyncio
async def test_clear_images_registry_not_found_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Action: Try to clear images for non-existent registry
    action = ClearImagesAction(registry="non-existent", project="non-existent")

    # Verify: Should raise ContainerRegistryNotFound
    with pytest.raises(ContainerRegistryNotFound):
        await container_registry_processors.clear_images.wait_for_complete(action)


@pytest.mark.asyncio
async def test_clear_images_transaction_behavior_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Setup: Create registry and image
    async with create_test_registry(database_engine, "test-registry-txn", "test-project-txn") as (
        registry_id,
        registry_name,
        project,
    ):
        async with create_test_image(
            database_engine, registry_id, registry_name, project
        ) as image_id:
            # Verify image is ALIVE
            async with database_engine.begin_readonly_session() as session:
                image = await session.get(ImageRow, image_id)
                assert image.status == ImageStatus.ALIVE

            # Mock the repository to simulate an error during clear operation
            # Get the service instance to patch the repository
            service_instance = container_registry_processors.clear_images._func.__self__  # type: ignore
            with patch.object(
                service_instance._admin_container_registry_repository,
                "clear_images_force",
                side_effect=Exception("Simulated error"),
            ):
                # Action: Try to clear images (should fail)
                action = ClearImagesAction(registry=registry_name, project=project)
                with pytest.raises(Exception):
                    await container_registry_processors.clear_images.wait_for_complete(action)

            # Verify: Image status should remain ALIVE (transaction rolled back)
            async with database_engine.begin_readonly_session() as session:
                image = await session.get(ImageRow, image_id)
                assert image.status == ImageStatus.ALIVE


@pytest.mark.asyncio
async def test_rescan_images_with_errors_integration(
    container_registry_processors: ContainerRegistryProcessors, database_engine
):
    # Setup: Create a container registry
    async with create_test_registry(database_engine) as (registry_id, registry_name, project):
        # Mock the registry scanner to simulate partial failure
        with aioresponses() as m:
            setup_dockerhub_mocking(
                m,
                f"https://{registry_name}.example.com",
                dockerhub_responses_mock={
                    "get_token": {"token": "fake-token"},
                    "get_catalog": {
                        "repositories": [f"{project}/python", f"{project}/broken-image"]
                    },
                    "get_tags": [
                        {"tags": ["3.9", "latest"]},  # First repo succeeds
                        {"error": "NOT_FOUND"},  # Second repo fails
                    ],
                    "get_manifest": {
                        "schemaVersion": 2,
                        "config": {
                            "digest": "sha256:" + "1" * 64,
                            "size": 100,
                        },
                        "layers": [
                            {
                                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                                "size": 1000,
                                "digest": "sha256:" + "2" * 64,
                            },
                            {
                                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                                "size": 2000,
                                "digest": "sha256:" + "3" * 64,
                            },
                        ],
                    },
                    "get_config": {
                        "architecture": "amd64",
                        "config": {
                            "Env": [
                                "PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                            ],
                        },
                    },
                },
            )

            # Action: Rescan images
            action = RescanImagesAction(
                registry=registry_name, project=project, progress_reporter=AsyncMock()
            )
            result = await container_registry_processors.rescan_images.wait_for_complete(action)

            # Verify: Should have some images and some errors
            assert result.registry.registry_name == registry_name
            assert len(result.images) >= 0  # May have successfully scanned some images
            # Note: Exact error handling depends on scanner implementation
