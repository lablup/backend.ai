"""The scopes an image is read from: the graph for ownership, the registry for global."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy import Row

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import (
    ContainerRegistryEntityType,
    ContainerRegistryID,
)
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow, ImageStatus, ImageType
from ai.backend.manager.models.image.scopes import (
    ContainerRegistryImageOperationScope,
    GlobalImageOperationScope,
    ProjectImageOperationScope,
)
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.querier import (
    BatchQuerierResult,
    execute_batch_querier,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


async def _search(
    db: ExtendedAsyncSAEngine, scopes: list[OperationScope]
) -> BatchQuerierResult[Row[Any]]:
    querier = BatchQuerier(
        conditions=[], orders=[], pagination=OffsetPagination(limit=100, offset=0)
    )
    async with db.begin_readonly_session() as sess:
        return await execute_batch_querier(sess, sa.select(ImageRow), querier, scopes=scopes)


def _image(name: str, registry_id: uuid.UUID, registry_name: str) -> ImageRow:
    return ImageRow(
        name=f"{registry_name}/test_project/{name}",
        image=name.split(":")[0],
        tag=name.split(":")[1],
        registry=registry_name,
        registry_id=registry_id,
        project="test_project",
        architecture="x86_64",
        config_digest=f"sha256:{uuid.uuid4().hex}",
        size_bytes=1000,
        type=ImageType.COMPUTE,
        status=ImageStatus.ALIVE,
        accelerators=None,
        labels={},
        resources={},
    )


class TestImageScopedSearch:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                ContainerRegistryRow,
                ImageRow,
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> dict[str, uuid.UUID]:
        """One image created in a project, one in a registry marked global."""
        project_id = uuid.uuid4()
        owned_registry_id = uuid.uuid4()
        global_registry_id = uuid.uuid4()
        seeder = VirtualEntitySeeder()

        domain_name = "test-domain"

        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                DomainRow(
                    id=DomainID(uuid.uuid4()),
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=10,
                )
            )
            await sess.flush()
            sess.add(
                ProjectRow(
                    id=project_id,
                    name="test-project",
                    domain_name=domain_name,
                    description="Test project",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="default",
                    type=ProjectType.GENERAL,
                )
            )
            for registry_id, registry_name, is_global in (
                (owned_registry_id, "owned.example.com", False),
                (global_registry_id, "global.example.com", True),
            ):
                sess.add(
                    ContainerRegistryRow(
                        id=ContainerRegistryID(registry_id),
                        url=f"https://{registry_name}",
                        registry_name=registry_name,
                        type=ContainerRegistryType.DOCKER,
                        project="test_project",
                        is_global=is_global,
                    )
                )
            owned = _image("python:3.13", owned_registry_id, "owned.example.com")
            shared = _image("python:3.12", global_registry_id, "global.example.com")
            sess.add_all([owned, shared])
            await sess.flush()

            await seeder.create_in(
                sess,
                ImageEntityType(),
                owned.id,
                [
                    (ProjectEntityType(), project_id),
                    (ContainerRegistryEntityType(), owned_registry_id),
                ],
            )
            await seeder.provision(sess, ImageEntityType(), shared.id)
            await sess.commit()

            return {
                "project_id": project_id,
                "owned_registry_id": owned_registry_id,
                "global_registry_id": global_registry_id,
                "owned_image_id": owned.id,
                "shared_image_id": shared.id,
            }

    async def test_project_scope_reads_what_the_project_holds(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        result = await _search(
            db_with_cleanup,
            [ProjectImageOperationScope(project_id=ProjectID(test_data["project_id"]))],
        )
        assert [row.ImageRow.id for row in result.rows] == [test_data["owned_image_id"]]

    async def test_registry_scope_reads_what_the_registry_holds(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        result = await _search(
            db_with_cleanup,
            [
                ContainerRegistryImageOperationScope(
                    registry_id=ContainerRegistryID(test_data["owned_registry_id"])
                )
            ],
        )
        assert [row.ImageRow.id for row in result.rows] == [test_data["owned_image_id"]]

    async def test_global_scope_reads_the_images_of_a_global_registry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """The global image is in no scope's graph, and is read all the same."""
        result = await _search(db_with_cleanup, [GlobalImageOperationScope()])
        assert [row.ImageRow.id for row in result.rows] == [test_data["shared_image_id"]]

    async def test_scopes_are_combined_with_or(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        result = await _search(
            db_with_cleanup,
            [
                ProjectImageOperationScope(project_id=ProjectID(test_data["project_id"])),
                GlobalImageOperationScope(),
            ],
        )
        assert {row.ImageRow.id for row in result.rows} == {
            test_data["owned_image_id"],
            test_data["shared_image_id"],
        }
