"""Regression test for ImagePermissionContextBuilder with non-global registries.

Reproduces the KeyError bug where querying images with a single project scope
crashes when a non-global registry is associated with multiple projects.
See: https://github.com/lablup/backend.ai/pull/10482
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.image.row import (
    ImagePermissionContextBuilder,
)
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.rbac.permission_defs import ImagePermission
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables

DOMAIN_NAME = "test-domain"
REGISTRY_URL = "https://cr.test.io"
REGISTRY_NAME = "cr.test.io"
USER_RESOURCE_POLICY_NAME = "test-user-policy"
PROJECT_RESOURCE_POLICY_NAME = "test-project-policy"


class TestImagePermissionContextNonGlobalRegistry:
    """Tests for ImagePermissionContextBuilder with non-global registry access control."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _create_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        name: str,
        domain: str,
        user: UserRow,
    ) -> UUID:
        project_id = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                GroupRow(
                    id=project_id,
                    name=name,
                    domain_name=domain,
                    is_active=True,
                    resource_policy=PROJECT_RESOURCE_POLICY_NAME,
                )
            )
            await sess.flush()
            sess.add(
                AssocGroupUserRow(
                    id=uuid4(),
                    user_id=user.uuid,
                    group_id=project_id,
                )
            )
            await sess.commit()
        return project_id

    def _make_image(
        self,
        registry_id: UUID,
        project: str,
        name_suffix: str,
    ) -> ImageRow:
        return ImageRow(
            name=f"{REGISTRY_NAME}/{project}/{name_suffix}:latest",
            image=name_suffix,
            tag="latest",
            registry=REGISTRY_NAME,
            registry_id=registry_id,
            project=project,
            architecture="x86_64",
            config_digest=f"sha256:{uuid4().hex}",
            size_bytes=100_000,
            type=ImageType.COMPUTE,
            status=ImageStatus.ALIVE,
            labels={},
            resources={},
        )

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

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
                KeyPairRow,
                UserRow,
                GroupRow,
                AssocGroupUserRow,
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
                ImageRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                DomainRow(
                    name=DOMAIN_NAME,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[REGISTRY_NAME],
                    dotfiles=b"\x90",
                )
            )
            sess.add(
                ProjectResourcePolicyRow(
                    name=PROJECT_RESOURCE_POLICY_NAME,
                    max_vfolder_count=0,
                    max_quota_scope_size=0,
                    max_network_count=0,
                )
            )
            await sess.commit()
        return DOMAIN_NAME

    @pytest.fixture
    async def user(self, db_with_cleanup: ExtendedAsyncSAEngine, domain: str) -> UserRow:
        user_id = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                UserResourcePolicyRow(
                    name=USER_RESOURCE_POLICY_NAME,
                    max_vfolder_count=0,
                    max_quota_scope_size=0,
                    max_session_count_per_model_session=0,
                    max_customized_image_count=0,
                )
            )
            await sess.flush()
            sess.add(
                UserRow(
                    uuid=user_id,
                    username="testuser",
                    email="testuser@test.io",
                    domain_name=domain,
                    role=UserRole.USER,
                    resource_policy=USER_RESOURCE_POLICY_NAME,
                )
            )
            await sess.commit()

        async with db_with_cleanup.begin_readonly_session() as sess:
            return await sess.get_one(UserRow, user_id)

    @pytest.fixture
    async def queried_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: str, user: UserRow
    ) -> UUID:
        """The project used as the query scope."""
        return await self._create_project(db_with_cleanup, "queried-project", domain, user)

    @pytest.fixture
    async def other_associated_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: str, user: UserRow
    ) -> UUID:
        """Another project associated with the non-global registry, but NOT the query scope."""
        return await self._create_project(db_with_cleanup, "other-associated-project", domain, user)

    @pytest.fixture
    async def unassociated_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: str, user: UserRow
    ) -> UUID:
        """A project with NO association to the non-global registry."""
        return await self._create_project(db_with_cleanup, "unassociated-project", domain, user)

    @pytest.fixture
    async def global_registry_id(self, db_with_cleanup: ExtendedAsyncSAEngine) -> UUID:
        registry_id = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url=REGISTRY_URL,
                    registry_name=REGISTRY_NAME,
                    type=ContainerRegistryType.HARBOR2,
                    project="stable",
                    is_global=True,
                )
            )
            await sess.commit()
        return registry_id

    @pytest.fixture
    async def non_global_registry_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        queried_project: UUID,
        other_associated_project: UUID,
    ) -> UUID:
        """A non-global registry associated with both queried_project and other_associated_project."""
        registry_id = uuid4()
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url=REGISTRY_URL,
                    registry_name=REGISTRY_NAME,
                    type=ContainerRegistryType.HARBOR2,
                    project="community",
                    is_global=False,
                )
            )
            await sess.flush()
            for project_id in [queried_project, other_associated_project]:
                sess.add(
                    AssociationContainerRegistriesGroupsRow(
                        id=uuid4(),
                        registry_id=registry_id,
                        group_id=project_id,
                    )
                )
            await sess.commit()
        return registry_id

    @pytest.fixture
    async def global_image_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        global_registry_id: UUID,
    ) -> UUID:
        async with db_with_cleanup.begin_session() as sess:
            img = self._make_image(global_registry_id, "stable", "python")
            sess.add(img)
            await sess.flush()
            image_id = img.id
            await sess.commit()
        return image_id

    @pytest.fixture
    async def non_global_image_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        non_global_registry_id: UUID,
    ) -> UUID:
        async with db_with_cleanup.begin_session() as sess:
            img = self._make_image(non_global_registry_id, "community", "custom-env")
            sess.add(img)
            await sess.flush()
            image_id = img.id
            await sess.commit()
        return image_id

    @pytest.fixture
    def client_ctx(self, db_with_cleanup: ExtendedAsyncSAEngine, user: UserRow) -> ClientContext:
        return ClientContext(
            db=db_with_cleanup,
            domain_name=DOMAIN_NAME,
            user_id=user.uuid,
            user_role=UserRole.USER,
        )

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    async def test_no_keyerror_when_non_global_registry_associated_with_multiple_projects(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        client_ctx: ClientContext,
        queried_project: UUID,
        other_associated_project: UUID,
        global_image_id: UUID,
        non_global_image_id: UUID,
    ) -> None:
        """Regression: querying with a single project scope must not KeyError
        when the non-global registry is also associated with another project.

        Before the fix, iterating all associated projects of the registry
        caused a KeyError for projects outside the queried scope.
        See: https://github.com/lablup/backend.ai/pull/10482
        """
        async with db_with_cleanup.begin_readonly_session() as db_session:
            builder = ImagePermissionContextBuilder(db_session)
            # Before the fix, this raised KeyError(str(other_associated_project))
            perm_ctx = await builder.build(
                client_ctx,
                ProjectScope(project_id=queried_project),
                ImagePermission.READ_ATTRIBUTE,
            )

        assert perm_ctx.query_condition is not None

        allowed_ids = set(perm_ctx.object_id_to_additional_permission_map.keys())
        assert global_image_id in allowed_ids
        assert non_global_image_id in allowed_ids

    async def test_unassociated_project_cannot_see_non_global_registry_images(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        client_ctx: ClientContext,
        queried_project: UUID,
        other_associated_project: UUID,
        unassociated_project: UUID,
        global_image_id: UUID,
        non_global_image_id: UUID,
    ) -> None:
        """A project with no association to the non-global registry
        should not see its images, but should still see global registry images."""
        async with db_with_cleanup.begin_readonly_session() as db_session:
            builder = ImagePermissionContextBuilder(db_session)
            perm_ctx = await builder.build(
                client_ctx,
                ProjectScope(project_id=unassociated_project),
                ImagePermission.READ_ATTRIBUTE,
            )

        allowed_ids = set(perm_ctx.object_id_to_additional_permission_map.keys())
        assert global_image_id in allowed_ids
        assert non_global_image_id not in allowed_ids
