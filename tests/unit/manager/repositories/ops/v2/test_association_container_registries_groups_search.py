"""Registry/project associations use the standard search execution path."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Protocol

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.data.permission.types import Permission, RoleStatus
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.container_registry.types import (
    AssociationContainerRegistriesGroupsData,
    ContainerRegistryData,
)
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.association_container_registries_groups.searchable_fields import (
    AssociationContainerRegistriesGroupsSearchableFields,
)
from ai.backend.manager.models.association_container_registries_groups.searchers import (
    AssociationContainerRegistriesGroupsSearcher,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.resource_group.row import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.pagination import (
    CursorForwardPagination,
    NoPagination,
    OffsetPagination,
    QueryPagination,
)
from ai.backend.manager.models.specs.searcher import SearcherResult
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

# Register the ORM relationship cluster before SQLAlchemy configures the mappers.
_ORM_CLUSTER = (AgentRow, ResourceGroupForDomainRow)


class GrantRead(Protocol):
    async def __call__(
        self,
        entity: EntityIdentifier,
        *,
        permission: Permission = Permission.READ,
        status: RoleStatus = RoleStatus.ACTIVE,
        cap: Permission | None = None,
        all_fields: bool = True,
        share_cap: Permission | None = None,
    ) -> None: ...


class TestAssociationContainerRegistriesGroupsSearcher:
    @pytest.fixture
    async def database(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                VirtualEntityRow,
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                UserRow,
                ProjectRow,
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
                RoleRow,
                UserRoleRow,
                PermissionRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def provider(self, database: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
        return V2DBOpsProvider(database)

    @pytest.fixture
    async def user_factory(
        self, database: ExtendedAsyncSAEngine, domain_factory: DomainFactory
    ) -> Callable[[UserRole], Awaitable[UserID]]:
        domain = await domain_factory(database)
        policy = "association-reader-policy"
        async with database.begin_session() as session:
            session.add(
                UserResourcePolicyRow(
                    name=policy,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=0,
                    max_customized_image_count=0,
                )
            )

        async def create_user(role: UserRole) -> UserID:
            user_id = UserID(uuid.uuid4())
            async with database.begin_session() as session:
                session.add(
                    UserRow(
                        uuid=user_id,
                        username=str(user_id),
                        email=f"{user_id}@example.com",
                        resource_policy=policy,
                        role=role,
                        need_password_change=False,
                        sudo_session_enabled=False,
                        domain_name=domain.domain_name,
                        domain_id=domain.domain_id,
                    )
                )
            return user_id

        return create_user

    @pytest.fixture
    async def superadmin(self, user_factory: Callable[[UserRole], Awaitable[UserID]]) -> UserID:
        return await user_factory(UserRole.SUPERADMIN)

    @pytest.fixture
    async def viewer(self, user_factory: Callable[[UserRole], Awaitable[UserID]]) -> UserID:
        return await user_factory(UserRole.USER)

    @pytest.fixture
    def grant_read(self, database: ExtendedAsyncSAEngine, viewer: UserID) -> GrantRead:
        async def grant(
            entity: EntityIdentifier,
            *,
            permission: Permission = Permission.READ,
            status: RoleStatus = RoleStatus.ACTIVE,
            cap: Permission | None = None,
            all_fields: bool = True,
            share_cap: Permission | None = None,
        ) -> None:
            async with database.begin_session() as session:
                seeder = VirtualEntitySeeder()
                node = await seeder.provision(session, entity.entity_type(), entity)
                scope = entity
                if share_cap is not None:
                    scope = viewer
                    holder = await seeder.provision(session, viewer.entity_type(), viewer)
                    await seeder.cap_edge(session, holder, node, share_cap)
                role_id = RoleID(uuid.uuid4())
                session.add(
                    RoleRow(
                        id=role_id,
                        name=str(role_id),
                        status=status,
                        scope_type=scope.entity_type(),
                        scope_id=scope,
                    )
                )
                await session.flush()
                session.add(UserRoleRow(user_id=viewer, role_id=role_id))
                session.add(
                    PermissionRow(
                        role_id=role_id,
                        entity_type=entity.entity_type(),
                        permission=permission,
                        all_fields=all_fields,
                    )
                )
                if cap is not None:
                    await session.execute(
                        sa.update(ScopeBindingRow)
                        .where(
                            ScopeBindingRow.virtual_entity_id == node,
                            ScopeBindingRow.scope_entity_id == node,
                        )
                        .values(permission_cap=int(cap))
                    )

        return grant

    @pytest.fixture
    async def project_factory(
        self, database: ExtendedAsyncSAEngine, domain_factory: DomainFactory
    ) -> Callable[[], Awaitable[ProjectID]]:
        domain = await domain_factory(database)
        policy_name = "default-registry-test-policy"
        async with database.begin_session() as session:
            session.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )

        async def create_project() -> ProjectID:
            project_id = ProjectID(uuid.uuid4())
            async with database.begin_session() as session:
                session.add(
                    ProjectRow(
                        id=project_id,
                        name=f"project-{project_id}",
                        domain_name=domain.domain_name,
                        resource_policy=policy_name,
                        total_resource_slots=ResourceSlot(),
                        container_registry={"registry": "legacy-only", "project": "unrelated"},
                    )
                )
            return project_id

        return create_project

    @pytest.fixture
    def registry_factory(
        self, database: ExtendedAsyncSAEngine
    ) -> Callable[[str], Awaitable[ContainerRegistryData]]:
        async def create_registry(label: str) -> ContainerRegistryData:
            registry = ContainerRegistryData(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{label}.example.com",
                registry_name="same-name",
                type=ContainerRegistryType.HARBOR2,
                project="same-registry-project",
                username=f"user-{label}",
                password=f"password-{label}",
                ssl_verify=True,
                is_global=False,
                extra={"label": label},
            )
            async with database.begin_session() as session:
                session.add(
                    ContainerRegistryRow(
                        id=registry.id,
                        url=registry.url,
                        registry_name=registry.registry_name,
                        type=registry.type,
                        project=registry.project,
                        username=registry.username,
                        password=registry.password,
                        ssl_verify=registry.ssl_verify,
                        is_global=registry.is_global,
                        extra=registry.extra,
                    )
                )
            return registry

        return create_registry

    @pytest.fixture
    async def default_registry(
        self, registry_factory: Callable[[str], Awaitable[ContainerRegistryData]]
    ) -> ContainerRegistryData:
        return await registry_factory("default")

    @pytest.fixture
    async def same_name_registry(
        self, registry_factory: Callable[[str], Awaitable[ContainerRegistryData]]
    ) -> ContainerRegistryData:
        return await registry_factory("same-name")

    @pytest.fixture
    async def project(self, project_factory: Callable[[], Awaitable[ProjectID]]) -> ProjectID:
        return await project_factory()

    @pytest.fixture
    async def another_project(
        self, project_factory: Callable[[], Awaitable[ProjectID]]
    ) -> ProjectID:
        return await project_factory()

    @pytest.fixture
    def association_factory(
        self, database: ExtendedAsyncSAEngine
    ) -> Callable[
        [ProjectID, ContainerRegistryID, bool], Awaitable[AssociationContainerRegistriesGroupsData]
    ]:
        async def create_association(
            project_id: ProjectID, registry_id: ContainerRegistryID, is_default: bool
        ) -> AssociationContainerRegistriesGroupsData:
            association = AssociationContainerRegistriesGroupsData(
                id=uuid.uuid4(),
                group_id=project_id,
                registry_id=registry_id,
                is_default=is_default,
            )
            async with database.begin_session() as session:
                session.add(
                    AssociationContainerRegistriesGroupsRow(
                        id=association.id,
                        group_id=association.group_id,
                        registry_id=association.registry_id,
                        is_default=association.is_default,
                    )
                )
            return association

        return create_association

    @pytest.fixture
    async def default_association(
        self,
        association_factory: Callable[
            [ProjectID, ContainerRegistryID, bool],
            Awaitable[AssociationContainerRegistriesGroupsData],
        ],
        project: ProjectID,
        default_registry: ContainerRegistryData,
    ) -> AssociationContainerRegistriesGroupsData:
        return await association_factory(project, default_registry.id, True)

    @pytest.fixture
    async def non_default_association(
        self,
        association_factory: Callable[
            [ProjectID, ContainerRegistryID, bool],
            Awaitable[AssociationContainerRegistriesGroupsData],
        ],
        project: ProjectID,
        same_name_registry: ContainerRegistryData,
    ) -> AssociationContainerRegistriesGroupsData:
        return await association_factory(project, same_name_registry.id, False)

    @pytest.fixture
    async def another_project_association(
        self,
        association_factory: Callable[
            [ProjectID, ContainerRegistryID, bool],
            Awaitable[AssociationContainerRegistriesGroupsData],
        ],
        another_project: ProjectID,
        default_registry: ContainerRegistryData,
    ) -> AssociationContainerRegistriesGroupsData:
        return await association_factory(another_project, default_registry.id, True)

    async def test_project_filter_returns_default_and_non_default_associations(
        self,
        provider: V2DBOpsProvider,
        superadmin: UserID,
        project: ProjectID,
        default_association: AssociationContainerRegistriesGroupsData,
        non_default_association: AssociationContainerRegistriesGroupsData,
        another_project_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=superadmin,
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[project])
                        ),
                    ],
                )
            )
        assert {item.id: item for item in found.items} == {
            default_association.id: default_association,
            non_default_association.id: non_default_association,
        }
        assert found.total_count == 2
        assert not found.has_next_page and not found.has_previous_page

    @pytest.mark.parametrize("is_default", [True, False])
    async def test_default_filter(
        self,
        provider: V2DBOpsProvider,
        superadmin: UserID,
        project: ProjectID,
        is_default: bool,
        default_association: AssociationContainerRegistriesGroupsData,
        non_default_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=superadmin,
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[project])
                        ),
                        AssociationContainerRegistriesGroupsSearchableFields.own.is_default.filter.equals(
                            is_default
                        ),
                    ],
                )
            )
        assert found == SearcherResult(
            items=[default_association if is_default else non_default_association],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

    async def test_shared_registry_keeps_each_project_association(
        self,
        provider: V2DBOpsProvider,
        superadmin: UserID,
        project: ProjectID,
        another_project: ProjectID,
        default_association: AssociationContainerRegistriesGroupsData,
        another_project_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=superadmin,
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[project, another_project])
                        ),
                        AssociationContainerRegistriesGroupsSearchableFields.own.is_default.filter.equals(
                            True
                        ),
                    ],
                )
            )
        assert {item.id: item for item in found.items} == {
            default_association.id: default_association,
            another_project_association.id: another_project_association,
        }
        assert found.total_count == 2
        assert not found.has_next_page and not found.has_previous_page

    async def test_project_without_association_returns_empty_result(
        self,
        provider: V2DBOpsProvider,
        superadmin: UserID,
        project: ProjectID,
        another_project_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=superadmin,
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[project])
                        ),
                    ],
                )
            )
        assert found == SearcherResult(
            items=[], total_count=0, has_next_page=False, has_previous_page=False
        )

    async def test_empty_project_filter_returns_empty_result(
        self,
        provider: V2DBOpsProvider,
        superadmin: UserID,
        default_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=superadmin,
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[])
                        ),
                    ],
                )
            )
        assert found == SearcherResult(
            items=[], total_count=0, has_next_page=False, has_previous_page=False
        )

    @pytest.mark.parametrize(
        ("project_read", "registry_read"),
        [(True, True), (True, False), (False, True), (False, False)],
    )
    @pytest.mark.parametrize("pagination", [NoPagination(), OffsetPagination(limit=1)])
    async def test_requires_read_on_both_entities(
        self,
        provider: V2DBOpsProvider,
        viewer: UserID,
        grant_read: GrantRead,
        default_association: AssociationContainerRegistriesGroupsData,
        project_read: bool,
        registry_read: bool,
        pagination: QueryPagination,
    ) -> None:
        if project_read:
            await grant_read(default_association.group_id)
        if registry_read:
            await grant_read(default_association.registry_id)
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=viewer,
                    pagination=pagination,
                )
            )
        expected = [default_association] if project_read and registry_read else []
        assert found == SearcherResult(
            items=expected,
            total_count=len(expected),
            has_next_page=False,
            has_previous_page=False,
        )

    @pytest.mark.parametrize("side", ["project", "registry"])
    @pytest.mark.parametrize(
        "restriction", ["inactive_role", "govern_cap", "update_only", "field_only"]
    )
    async def test_read_restrictions_on_either_entity(
        self,
        provider: V2DBOpsProvider,
        viewer: UserID,
        grant_read: GrantRead,
        default_association: AssociationContainerRegistriesGroupsData,
        side: str,
        restriction: str,
    ) -> None:
        restricted, other = (
            (default_association.group_id, default_association.registry_id)
            if side == "project"
            else (default_association.registry_id, default_association.group_id)
        )
        await grant_read(other)
        await grant_read(
            restricted,
            permission=Permission.UPDATE if restriction == "update_only" else Permission.READ,
            status=RoleStatus.INACTIVE if restriction == "inactive_role" else RoleStatus.ACTIVE,
            cap=Permission.UPDATE if restriction == "govern_cap" else None,
            all_fields=restriction != "field_only",
        )
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=viewer,
                    pagination=NoPagination(),
                )
            )
        assert found == SearcherResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )

    @pytest.mark.parametrize("offset", [0, 1])
    @pytest.mark.parametrize("cursor", [False, True])
    async def test_permissions_filter_before_pagination_and_count(
        self,
        provider: V2DBOpsProvider,
        viewer: UserID,
        grant_read: GrantRead,
        default_association: AssociationContainerRegistriesGroupsData,
        non_default_association: AssociationContainerRegistriesGroupsData,
        another_project_association: AssociationContainerRegistriesGroupsData,
        offset: int,
        cursor: bool,
    ) -> None:
        await grant_read(default_association.group_id)
        await grant_read(default_association.registry_id)
        pagination: QueryPagination = OffsetPagination(limit=1, offset=offset)
        if cursor:
            pagination = CursorForwardPagination(
                first=1,
                cursor_order=AssociationContainerRegistriesGroupsRow.id.asc(),
                cursor_condition=(
                    (lambda: AssociationContainerRegistriesGroupsRow.id > default_association.id)
                    if offset
                    else None
                ),
            )
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=viewer,
                    pagination=pagination,
                    orders=[AssociationContainerRegistriesGroupsRow.is_default.asc()],
                )
            )
        assert found == SearcherResult(
            items=[default_association] if offset == 0 else [],
            total_count=1,
            has_next_page=False,
            has_previous_page=offset > 0,
        )

    async def test_multiple_grants_do_not_duplicate_associations(
        self,
        provider: V2DBOpsProvider,
        viewer: UserID,
        grant_read: GrantRead,
        default_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        for entity in (default_association.group_id, default_association.registry_id):
            await grant_read(entity)
            await grant_read(entity)
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=viewer,
                    pagination=OffsetPagination(limit=1),
                )
            )
        assert found == SearcherResult(
            items=[default_association],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

    @pytest.mark.parametrize("side", ["project", "registry"])
    @pytest.mark.parametrize("share_cap", [Permission.READ, Permission.UPDATE])
    async def test_share_cap_on_either_entity(
        self,
        provider: V2DBOpsProvider,
        viewer: UserID,
        grant_read: GrantRead,
        default_association: AssociationContainerRegistriesGroupsData,
        side: str,
        share_cap: Permission,
    ) -> None:
        shared, other = (
            (default_association.group_id, default_association.registry_id)
            if side == "project"
            else (default_association.registry_id, default_association.group_id)
        )
        await grant_read(other)
        await grant_read(shared, share_cap=share_cap)
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    user_id=viewer,
                    pagination=OffsetPagination(limit=1),
                )
            )
        expected = [default_association] if share_cap == Permission.READ else []
        assert found == SearcherResult(
            items=expected,
            total_count=len(expected),
            has_next_page=False,
            has_previous_page=False,
        )
