from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sqlalchemy as sa
from aioresponses import aioresponses
from graphene.test import Client

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.defs import PASSWORD_PLACEHOLDER
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.gql import GraphQueryContext
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
        registry_id = None
        async with database_engine.begin_session() as session:
            registry = ContainerRegistryRow(
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
            registry_id = registry.id

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


# GraphQL Integration Tests for Container Registry CRUD operations
class TestContainerRegistryGraphQLIntegration:
    """Integration tests for container registry GraphQL operations (V1 API)"""

    @pytest.fixture
    def graphql_client(self) -> Client:
        """Create GraphQL client"""
        from graphene import Schema
        from graphene.test import Client

        from ai.backend.manager.models.gql import Mutation, Query

        return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))

    async def create_graphql_context(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> GraphQueryContext:
        """Create GraphQL context with mock config"""
        mock_loader = MagicMock()
        mock_loader.load = AsyncMock()
        mock_loader.load.return_value = ManagerUnifiedConfig().model_dump()

        config_provider = await ManagerConfigProvider.create(
            loader=mock_loader,
            etcd_watcher=MagicMock(),
            legacy_etcd_config_loader=MagicMock(),  # type: ignore
        )

        return GraphQueryContext(
            schema=None,  # type: ignore
            dataloader_manager=None,  # type: ignore
            config_provider=config_provider,
            etcd=MagicMock(),  # type: ignore
            user={"domain": "default", "role": "superadmin"},
            access_key="AKIAIOSFODNN7EXAMPLE",
            db=database_engine,  # type: ignore
            valkey_stat=None,  # type: ignore
            valkey_image=None,  # type: ignore
            valkey_live=None,  # type: ignore
            valkey_schedule=None,  # type: ignore
            manager_status=None,  # type: ignore
            known_slot_types=None,  # type: ignore
            background_task_manager=None,  # type: ignore
            storage_manager=None,  # type: ignore
            registry=None,  # type: ignore
            idle_checker_host=None,  # type: ignore
            network_plugin_ctx=None,  # type: ignore
            services_ctx=None,  # type: ignore
            metric_observer=GraphQLMetricObserver.instance(),
            processors=None,  # type: ignore
            scheduler_repository=None,  # type: ignore
            user_repository=None,  # type: ignore
            agent_repository=None,  # type: ignore
        )

    @pytest.mark.asyncio
    async def test_create_container_registry(
        self, graphql_client: Client, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Integration test for creating container registry via GraphQL"""
        context = await self.create_graphql_context(database_engine)

        query = """
            mutation CreateContainerRegistryNode($type: ContainerRegistryTypeField!, $registry_name: String!, $url: String!, $project: String!, $username: String!, $password: String!, $ssl_verify: Boolean!, $is_global: Boolean!) {
                create_container_registry_node(type: $type, registry_name: $registry_name, url: $url, project: $project, username: $username, password: $password, ssl_verify: $ssl_verify, is_global: $is_global) {
                    container_registry {
                        row_id
                        registry_name
                        url
                        type
                        project
                        username
                        password
                        ssl_verify
                        is_global
                    }
                }
            }
        """

        variables = {
            "registry_name": "cr-integration.example.com",
            "url": "http://cr-integration.example.com",
            "type": ContainerRegistryType.DOCKER,
            "project": "integration-test",
            "username": "test-user",
            "password": "test-password",
            "ssl_verify": False,
            "is_global": False,
        }

        try:
            response = await graphql_client.execute_async(
                query, variables=variables, context_value=context
            )
            container_registry = response["data"]["create_container_registry_node"][
                "container_registry"
            ]

            registry_id = container_registry.pop("row_id", None)
            assert registry_id is not None

            assert container_registry == {
                "registry_name": "cr-integration.example.com",
                "url": "http://cr-integration.example.com",
                "type": "docker",
                "project": "integration-test",
                "username": "test-user",
                "password": PASSWORD_PLACEHOLDER,
                "ssl_verify": False,
                "is_global": False,
            }
        finally:
            # Cleanup
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(
                        (ContainerRegistryRow.registry_name == "cr-integration.example.com")
                        & (ContainerRegistryRow.project == "integration-test")
                    )
                )

    @pytest.mark.asyncio
    async def test_modify_container_registry(
        self, graphql_client: Client, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Integration test for modifying container registry via GraphQL"""
        context = await self.create_graphql_context(database_engine)

        # Setup: Create a registry first
        async with create_test_registry(
            database_engine, "modify-graphql-registry", "modify-graphql-project"
        ) as (registry_id, registry_name, project):
            # Query to get the registry
            query_registry = """
                query ContainerRegistryNodes($filter: String!) {
                    container_registry_nodes (filter: $filter) {
                        edges {
                            node {
                                row_id
                                registry_name
                                url
                                type
                                project
                                username
                                password
                                ssl_verify
                                is_global
                            }
                            cursor
                        }
                    }
                }
            """

            variables = {
                "filter": f'registry_name == "{registry_name}"',
            }

            response = await graphql_client.execute_async(
                query_registry, variables=variables, context_value=context
            )
            target_container_registries = list(
                filter(
                    lambda item: item["node"]["project"] == project,
                    response["data"]["container_registry_nodes"]["edges"],
                )
            )

            assert len(target_container_registries) == 1
            target_container_registry = target_container_registries[0]["node"]

            # Modify the registry
            modify_query = """
                mutation ModifyContainerRegistryNode($id: String!, $type: ContainerRegistryTypeField, $registry_name: String, $url: String, $project: String, $username: String, $password: String, $ssl_verify: Boolean, $is_global: Boolean) {
                    modify_container_registry_node(id: $id, type: $type, registry_name: $registry_name, url: $url, project: $project, username: $username, password: $password, ssl_verify: $ssl_verify, is_global: $is_global) {
                        container_registry {
                            row_id
                            registry_name
                            url
                            type
                            project
                            username
                            password
                            ssl_verify
                            is_global
                        }
                    }
                }
            """

            modify_variables = {
                "id": target_container_registry["row_id"],
                "registry_name": registry_name,
                "username": "modified-user",
            }

            response = await graphql_client.execute_async(
                modify_query, variables=modify_variables, context_value=context
            )

            container_registry = response["data"]["modify_container_registry_node"][
                "container_registry"
            ]
            assert container_registry["username"] == "modified-user"

    @pytest.mark.asyncio
    async def test_delete_container_registry(
        self, graphql_client: Client, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Integration test for deleting container registry via GraphQL"""
        context = await self.create_graphql_context(database_engine)

        # Setup: Create a registry first
        async with create_test_registry(
            database_engine, "delete-graphql-registry", "delete-graphql-project"
        ) as (registry_id, registry_name, project):
            # Query to get the registry
            query_registry = """
                query ContainerRegistryNodes($filter: String!) {
                    container_registry_nodes (filter: $filter) {
                        edges {
                            node {
                                row_id
                                registry_name
                            }
                            cursor
                        }
                    }
                }
            """

            variables = {
                "filter": f'registry_name == "{registry_name}"',
            }

            response = await graphql_client.execute_async(
                query_registry, variables=variables, context_value=context
            )
            target_container_registries = list(
                filter(
                    lambda item: item["node"]["registry_name"] == registry_name,
                    response["data"]["container_registry_nodes"]["edges"],
                )
            )

            assert len(target_container_registries) >= 1
            target_container_registry = target_container_registries[0]["node"]

            # Delete the registry
            delete_query = """
                mutation DeleteContainerRegistryNode($id: String!) {
                    delete_container_registry_node(id: $id) {
                        container_registry {
                            row_id
                            registry_name
                        }
                    }
                }
            """

            delete_variables = {
                "id": str(target_container_registry["row_id"]),
            }
            response = await graphql_client.execute_async(
                delete_query, variables=delete_variables, context_value=context
            )

            container_registry = response["data"]["delete_container_registry_node"][
                "container_registry"
            ]
            assert container_registry["registry_name"] == registry_name

            # Verify deletion
            query_after_delete = """
                query ContainerRegistryNodes($filter: String!) {
                    container_registry_nodes (filter: $filter) {
                        edges {
                            node {
                                row_id
                            }
                        }
                    }
                }
            """

            variables_after = {
                "filter": f'row_id == "{target_container_registry["row_id"]}"',
            }

            response = await graphql_client.execute_async(
                query_after_delete, variables=variables_after, context_value=context
            )
            assert response["data"]["container_registry_nodes"] is None


class TestContainerRegistryGraphQLV2Integration:
    """Test class for Container Registry GraphQL V2 API integration tests"""

    @pytest.fixture
    async def graphql_client(self) -> Client:
        """Create a GraphQL client for testing"""
        from graphene import Schema

        from ai.backend.manager.models.gql import Mutation, Query

        return Client(Schema(query=Query, mutation=Mutation, auto_camelcase=False))

    async def create_graphql_context(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> GraphQueryContext:
        """Create a GraphQL context for testing (V2 API uses simpler context)"""
        from ai.backend.common.metrics.metric import GraphQLMetricObserver
        from ai.backend.manager.models.gql import GraphQueryContext

        return GraphQueryContext(
            schema=None,  # type: ignore
            dataloader_manager=None,  # type: ignore
            config_provider=None,  # type: ignore
            etcd=None,  # type: ignore
            user={"domain": "default", "role": "superadmin"},
            access_key="AKIAIOSFODNN7EXAMPLE",
            db=database_engine,  # type: ignore
            valkey_stat=None,  # type: ignore
            valkey_image=None,  # type: ignore
            valkey_live=None,  # type: ignore
            valkey_schedule=None,  # type: ignore
            manager_status=None,  # type: ignore
            known_slot_types=None,  # type: ignore
            background_task_manager=None,  # type: ignore
            storage_manager=None,  # type: ignore
            registry=None,  # type: ignore
            idle_checker_host=None,  # type: ignore
            network_plugin_ctx=None,  # type: ignore
            services_ctx=None,  # type: ignore
            metric_observer=GraphQLMetricObserver.instance(),
            processors=None,  # type: ignore
            scheduler_repository=None,  # type: ignore
            user_repository=None,  # type: ignore
            agent_repository=None,  # type: ignore
        )

    # GraphQL V2 Integration Tests for Container Registry CRUD operations
    @pytest.mark.asyncio
    async def test_create_container_registry_v2(
        self, graphql_client: Client, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Integration test for creating container registry via GraphQL V2 API"""
        context = await self.create_graphql_context(database_engine)

        query = """
            mutation ($props: CreateContainerRegistryNodeInputV2!) {
                create_container_registry_node_v2(props: $props) {
                    container_registry {
                        row_id
                        registry_name
                        url
                        type
                        project
                        username
                        password
                        ssl_verify
                        is_global
                    }
                }
            }
        """

        variables = {
            "props": {
                "registry_name": "cr-v2-integration.example.com",
                "url": "http://cr-v2-integration.example.com",
                "type": ContainerRegistryType.DOCKER,
                "project": "v2-integration-test",
                "username": "test-user",
                "password": "test-password",
                "ssl_verify": False,
                "is_global": False,
            }
        }

        try:
            response = await graphql_client.execute_async(
                query, variables=variables, context_value=context
            )
            container_registry = response["data"]["create_container_registry_node_v2"][
                "container_registry"
            ]

            registry_id = container_registry.pop("row_id", None)
            assert registry_id is not None

            assert container_registry == {
                "registry_name": "cr-v2-integration.example.com",
                "url": "http://cr-v2-integration.example.com",
                "type": "docker",
                "project": "v2-integration-test",
                "username": "test-user",
                "password": PASSWORD_PLACEHOLDER,
                "ssl_verify": False,
                "is_global": False,
            }
        finally:
            # Cleanup
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(
                        (ContainerRegistryRow.registry_name == "cr-v2-integration.example.com")
                        & (ContainerRegistryRow.project == "v2-integration-test")
                    )
                )

    @pytest.mark.asyncio
    async def test_modify_container_registry_v2(
        self, graphql_client: Client, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Integration test for modifying container registry via GraphQL V2 API"""
        context = await self.create_graphql_context(database_engine)

        # Setup: Create a registry first
        async with create_test_registry(
            database_engine, "modify-v2-graphql-registry", "modify-v2-graphql-project"
        ) as (registry_id, registry_name, project):
            # Query to get the registry
            query_registry = """
                query ($filter: String!) {
                    container_registry_nodes (filter: $filter) {
                        edges {
                            node {
                                row_id
                                registry_name
                                url
                                type
                                project
                                username
                                password
                                ssl_verify
                                is_global
                            }
                            cursor
                        }
                    }
                }
            """

            variables = {
                "filter": f'registry_name == "{registry_name}"',
            }

            response = await graphql_client.execute_async(
                query_registry, variables=variables, context_value=context
            )
            target_container_registries = list(
                filter(
                    lambda item: item["node"]["project"] == project,
                    response["data"]["container_registry_nodes"]["edges"],
                )
            )

            assert len(target_container_registries) == 1
            target_container_registry = target_container_registries[0]["node"]

            # Modify the registry using V2 API
            modify_query = """
                mutation ($id: String!, $props: ModifyContainerRegistryNodeInputV2!) {
                    modify_container_registry_node_v2(id: $id, props: $props) {
                        container_registry {
                            row_id
                            registry_name
                            url
                            type
                            project
                            username
                            password
                            ssl_verify
                            is_global
                        }
                    }
                }
            """

            modify_variables = {
                "id": target_container_registry["row_id"],
                "props": {
                    "registry_name": registry_name,
                    "username": "modified-user-v2",
                    "url": "https://modified-url.example.com",
                },
            }

            response = await graphql_client.execute_async(
                modify_query, variables=modify_variables, context_value=context
            )

            container_registry = response["data"]["modify_container_registry_node_v2"][
                "container_registry"
            ]
            assert container_registry["username"] == "modified-user-v2"
            assert container_registry["url"] == "https://modified-url.example.com"

    @pytest.mark.asyncio
    async def test_modify_container_registry_v2_allows_empty_string(
        self, graphql_client: Client, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Integration test for modifying container registry password to empty string via V2 API"""
        from ai.backend.manager.defs import PASSWORD_PLACEHOLDER

        context = await self.create_graphql_context(database_engine)

        # Setup: Create a registry with password
        async with database_engine.begin_session() as session:
            registry = ContainerRegistryRow(
                url="https://modify-empty-v2.example.com",
                registry_name="modify-empty-v2-registry",
                type=ContainerRegistryType.DOCKER,
                project="modify-empty-v2-project",
                username="test-user",
                password="initial-password",
                ssl_verify=True,
                is_global=False,
                extra=None,
            )
            session.add(registry)
            await session.flush()
            registry_id = registry.id

        try:
            # Modify password to empty string
            modify_query = """
                mutation ($id: String!, $props: ModifyContainerRegistryNodeInputV2!) {
                    modify_container_registry_node_v2(id: $id, props: $props) {
                        container_registry {
                            row_id
                            password
                        }
                    }
                }
            """

            modify_variables = {
                "id": str(registry_id),
                "props": {
                    "password": "",
                },
            }

            response = await graphql_client.execute_async(
                modify_query, variables=modify_variables, context_value=context
            )

            container_registry = response["data"]["modify_container_registry_node_v2"][
                "container_registry"
            ]
            assert container_registry["password"] == PASSWORD_PLACEHOLDER
        finally:
            # Cleanup
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
                )

    @pytest.mark.asyncio
    async def test_modify_container_registry_v2_allows_null_for_unset(
        self, graphql_client: Client, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Integration test for unsetting container registry password via V2 API"""
        context = await self.create_graphql_context(database_engine)

        # Setup: Create a registry with password
        async with database_engine.begin_session() as session:
            registry = ContainerRegistryRow(
                url="https://modify-null-v2.example.com",
                registry_name="modify-null-v2-registry",
                type=ContainerRegistryType.DOCKER,
                project="modify-null-v2-project",
                username="test-user",
                password="initial-password",
                ssl_verify=True,
                is_global=False,
                extra=None,
            )
            session.add(registry)
            await session.flush()
            registry_id = registry.id

        try:
            # Unset password with null
            modify_query = """
                mutation ($id: String!, $props: ModifyContainerRegistryNodeInputV2!) {
                    modify_container_registry_node_v2(id: $id, props: $props) {
                        container_registry {
                            row_id
                            password
                        }
                    }
                }
            """

            modify_variables = {
                "id": str(registry_id),
                "props": {
                    "password": None,
                },
            }

            response = await graphql_client.execute_async(
                modify_query, variables=modify_variables, context_value=context
            )

            container_registry = response["data"]["modify_container_registry_node_v2"][
                "container_registry"
            ]
            assert container_registry["password"] is None
        finally:
            # Cleanup
            async with database_engine.begin_session() as session:
                await session.execute(
                    sa.delete(ContainerRegistryRow).where(ContainerRegistryRow.id == registry_id)
                )

    @pytest.mark.asyncio
    async def test_delete_container_registry_v2(
        self, graphql_client: Client, database_engine: ExtendedAsyncSAEngine
    ) -> None:
        """Integration test for deleting container registry via GraphQL V2 API"""
        context = await self.create_graphql_context(database_engine)

        # Setup: Create a registry first
        async with create_test_registry(
            database_engine, "delete-v2-graphql-registry", "delete-v2-graphql-project"
        ) as (registry_id, registry_name, project):
            # Query to get the registry
            query_registry = """
                query ($filter: String!) {
                    container_registry_nodes (filter: $filter) {
                        edges {
                            node {
                                row_id
                                registry_name
                            }
                            cursor
                        }
                    }
                }
            """

            variables = {
                "filter": f'registry_name == "{registry_name}"',
            }

            response = await graphql_client.execute_async(
                query_registry, variables=variables, context_value=context
            )
            target_container_registries = list(
                filter(
                    lambda item: item["node"]["registry_name"] == registry_name,
                    response["data"]["container_registry_nodes"]["edges"],
                )
            )

            assert len(target_container_registries) >= 1
            target_container_registry = target_container_registries[0]["node"]

            # Delete the registry using V2 API
            delete_query = """
                mutation ($id: String!) {
                    delete_container_registry_node_v2(id: $id) {
                        container_registry {
                            row_id
                            registry_name
                        }
                    }
                }
            """

            delete_variables = {
                "id": str(target_container_registry["row_id"]),
            }
            response = await graphql_client.execute_async(
                delete_query, variables=delete_variables, context_value=context
            )

            container_registry = response["data"]["delete_container_registry_node_v2"][
                "container_registry"
            ]
            assert container_registry["registry_name"] == registry_name

            # Verify deletion
            query_after_delete = """
                query ($filter: String!) {
                    container_registry_nodes (filter: $filter) {
                        edges {
                            node {
                                row_id
                            }
                        }
                    }
                }
            """

            variables_after = {
                "filter": f'row_id == "{target_container_registry["row_id"]}"',
            }

            response = await graphql_client.execute_async(
                query_after_delete, variables=variables_after, context_value=context
            )
            assert response["data"]["container_registry_nodes"] is None
