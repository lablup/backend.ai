"""Regression tests for ImagePermissionContextBuilder.

Two crashes are covered here:

- Querying a single project scope raised KeyError when a non-global registry was
  associated with more than one project.
  See: https://github.com/lablup/backend.ai/pull/10482
- Querying the system scope raised IndexError when the caller belonged to no project,
  because global-registry images took their permissions from an arbitrary entry of the
  per-project permission map, which is empty in that case.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.permission.permission_defs import ImagePermission
from ai.backend.manager.data.permission.types import EntityType, RelationType
from ai.backend.manager.data.permission.types import ScopeType as PermissionScopeType

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.image.row import (
    ADMIN_PERMISSIONS,
    ALL_IMAGE_PERMISSIONS,
    MEMBER_PERMISSIONS,
    MONITOR_PERMISSIONS,
    PRIVILEGED_MEMBER_PERMISSIONS,
    ImagePermissionContextBuilder,
)
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac import ProjectScope, SystemScope
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.db import with_tables

DOMAIN_NAME = "test-domain"
REGISTRY_URL = "https://cr.test.io"
REGISTRY_NAME = "cr.test.io"
USER_RESOURCE_POLICY_NAME = "test-user-policy"
PROJECT_RESOURCE_POLICY_NAME = "test-project-policy"


_ORM_CLUSTER = (
    AgentRow,
    ScalingGroupForDomainRow,
)


async def _create_project(
    db: ExtendedAsyncSAEngine,
    name: str,
    domain: str,
    member: UserRow | None,
) -> UUID:
    """Create a project, joining `member` to it as a group member when given."""
    project_id = uuid4()
    async with db.begin_session() as sess:
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
        if member is not None:
            sess.add(
                AssocGroupUserRow(
                    id=uuid4(),
                    user_id=member.uuid,
                    group_id=project_id,
                )
            )
        await sess.commit()
    return project_id


@pytest.fixture
async def db_with_cleanup(
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
            AssociationScopesEntitiesRow,
            ContainerRegistryRow,
            AssociationContainerRegistriesGroupsRow,
            ImageRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def domain(db_with_cleanup: ExtendedAsyncSAEngine) -> str:
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
async def user(db_with_cleanup: ExtendedAsyncSAEngine, domain: str) -> UserRow:
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
async def global_registry_id(db_with_cleanup: ExtendedAsyncSAEngine) -> UUID:
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
async def global_image_id(
    db_with_cleanup: ExtendedAsyncSAEngine,
    global_registry_id: UUID,
) -> UUID:
    async with db_with_cleanup.begin_session() as sess:
        img = ImageRow(
            name=f"{REGISTRY_NAME}/stable/python:latest",
            image="python",
            tag="latest",
            registry=REGISTRY_NAME,
            registry_id=global_registry_id,
            project="stable",
            architecture="x86_64",
            config_digest=f"sha256:{uuid4().hex}",
            size_bytes=100_000,
            type=ImageType.COMPUTE,
            status=ImageStatus.ALIVE,
            labels={},
            resources={},
        )
        sess.add(img)
        await sess.flush()
        image_id = img.id
        await sess.commit()
    return image_id


class TestImagePermissionContextNonGlobalRegistry:
    """Tests for ImagePermissionContextBuilder with non-global registry access control."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture
    async def queried_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: str, user: UserRow
    ) -> UUID:
        """The project used as the query scope."""
        return await _create_project(db_with_cleanup, "queried-project", domain, user)

    @pytest.fixture
    async def other_associated_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: str, user: UserRow
    ) -> UUID:
        """Another project associated with the non-global registry, but NOT the query scope."""
        return await _create_project(db_with_cleanup, "other-associated-project", domain, user)

    @pytest.fixture
    async def unassociated_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: str, user: UserRow
    ) -> UUID:
        """A project with NO association to the non-global registry."""
        return await _create_project(db_with_cleanup, "unassociated-project", domain, user)

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
    async def non_global_image_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        non_global_registry_id: UUID,
    ) -> UUID:
        async with db_with_cleanup.begin_session() as sess:
            img = ImageRow(
                name=f"{REGISTRY_NAME}/community/custom-env:latest",
                image="custom-env",
                tag="latest",
                registry=REGISTRY_NAME,
                registry_id=non_global_registry_id,
                project="community",
                architecture="x86_64",
                config_digest=f"sha256:{uuid4().hex}",
                size_bytes=100_000,
                type=ImageType.COMPUTE,
                status=ImageStatus.ALIVE,
                labels={},
                resources={},
            )
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


@dataclass(frozen=True)
class _SystemScopeCase:
    """A caller's role and the permissions its global-registry images must carry."""

    user_role: UserRole
    expected_permissions: frozenset[ImagePermission]


class TestImagePermissionContextSystemScope:
    """Tests for ImagePermissionContextBuilder in the system scope.

    Global-registry images belong to no project, so their permissions must not be taken from
    an arbitrary project association.
    """

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------

    @pytest.fixture
    def case(self) -> _SystemScopeCase:
        """The caller for tests that do not vary the role; overridden by parametrize.

        A plain user that belongs to a project holds the privileged-member permissions there.
        """
        return _SystemScopeCase(
            user_role=UserRole.USER,
            expected_permissions=PRIVILEGED_MEMBER_PERMISSIONS,
        )

    @pytest.fixture
    def client_ctx(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        user: UserRow,
        case: _SystemScopeCase,
    ) -> ClientContext:
        return ClientContext(
            db=db_with_cleanup,
            domain_name=DOMAIN_NAME,
            user_id=user.uuid,
            user_role=case.user_role,
        )

    @pytest.fixture
    async def member_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine, domain: str, user: UserRow
    ) -> UUID:
        """A project the caller is a group member of."""
        return await _create_project(db_with_cleanup, "member-project", domain, user)

    @pytest.fixture
    async def non_member_project(self, db_with_cleanup: ExtendedAsyncSAEngine, domain: str) -> UUID:
        """A project the caller has an RBAC scope association with, but is not a member of.

        A plain user holds no permission in such a project.
        """
        return await _create_project(db_with_cleanup, "non-member-project", domain, None)

    @pytest.fixture
    async def scope_association_to_member_project(
        self, db_with_cleanup: ExtendedAsyncSAEngine, user: UserRow, member_project: UUID
    ) -> None:
        async with db_with_cleanup.begin_session() as sess:
            sess.add(
                AssociationScopesEntitiesRow(
                    id=uuid4(),
                    scope_type=PermissionScopeType.PROJECT,
                    scope_id=str(member_project),
                    entity_type=EntityType.USER,
                    entity_id=str(user.uuid),
                    relation_type=RelationType.AUTO,
                )
            )
            await sess.commit()

    @pytest.fixture
    async def scope_associations_to_both_projects(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        user: UserRow,
        member_project: UUID,
        non_member_project: UUID,
    ) -> None:
        async with db_with_cleanup.begin_session() as sess:
            for project_id in [member_project, non_member_project]:
                sess.add(
                    AssociationScopesEntitiesRow(
                        id=uuid4(),
                        scope_type=PermissionScopeType.PROJECT,
                        scope_id=str(project_id),
                        entity_type=EntityType.USER,
                        entity_id=str(user.uuid),
                        relation_type=RelationType.AUTO,
                    )
                )
            await sess.commit()

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "case",
        [
            _SystemScopeCase(
                user_role=UserRole.SUPERADMIN,
                expected_permissions=ALL_IMAGE_PERMISSIONS,
            ),
            _SystemScopeCase(
                user_role=UserRole.ADMIN,
                expected_permissions=ADMIN_PERMISSIONS,
            ),
            _SystemScopeCase(
                user_role=UserRole.USER,
                expected_permissions=MEMBER_PERMISSIONS,
            ),
            _SystemScopeCase(
                user_role=UserRole.MONITOR,
                expected_permissions=MONITOR_PERMISSIONS,
            ),
        ],
        ids=lambda case: case.user_role.value,
    )
    async def test_global_registry_images_visible_without_project_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        client_ctx: ClientContext,
        case: _SystemScopeCase,
        global_image_id: UUID,
    ) -> None:
        """Regression: a caller associated with no project must still get the global-registry
        images, carrying the permissions it holds in the system scope.

        Before the fix, this raised IndexError from an empty per-project permission map.
        """
        async with db_with_cleanup.begin_readonly_session() as db_session:
            builder = ImagePermissionContextBuilder(db_session)
            perm_ctx = await builder.build(
                client_ctx,
                SystemScope(),
                ImagePermission.READ_ATTRIBUTE,
            )

        assert perm_ctx.object_id_to_additional_permission_map == {
            global_image_id: case.expected_permissions
        }

    async def test_global_registry_images_visible_with_project_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        client_ctx: ClientContext,
        case: _SystemScopeCase,
        scope_association_to_member_project: None,
        global_image_id: UUID,
    ) -> None:
        """A caller associated with a project sees the global-registry images carrying the
        permissions it holds in that project."""
        async with db_with_cleanup.begin_readonly_session() as db_session:
            builder = ImagePermissionContextBuilder(db_session)
            perm_ctx = await builder.build(
                client_ctx,
                SystemScope(),
                ImagePermission.READ_ATTRIBUTE,
            )

        assert perm_ctx.object_id_to_additional_permission_map == {
            global_image_id: case.expected_permissions
        }

    async def test_global_registry_permissions_are_unioned_across_project_scopes(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        client_ctx: ClientContext,
        case: _SystemScopeCase,
        scope_associations_to_both_projects: None,
        global_image_id: UUID,
    ) -> None:
        """Permissions on global-registry images do not depend on which associated project scope
        happens to come first: the caller keeps the permissions of the project it is a member of
        even though it holds none in the other associated project."""
        async with db_with_cleanup.begin_readonly_session() as db_session:
            builder = ImagePermissionContextBuilder(db_session)
            perm_ctx = await builder.build(
                client_ctx,
                SystemScope(),
                ImagePermission.READ_ATTRIBUTE,
            )

        assert perm_ctx.object_id_to_additional_permission_map == {
            global_image_id: case.expected_permissions
        }
