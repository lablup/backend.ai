"""Tests for the idle checker bindings, written as a relation, against a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.data.permission.types import Permission, ScopeType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import ResourceSlot, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData, IdleCheckerData
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.idle_checker import (
    IdleCheckerAssignmentNotFound,
    IdleCheckerAssignmentScopeNotFound,
    IdleCheckerNotFound,
)
from ai.backend.manager.errors.repository import EmptyOperationScopeError
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.idle_checker.conditions import IdleCheckerAssignmentConditions
from ai.backend.manager.models.idle_checker.creators import (
    IdleCheckerAssignmentCreator,
    IdleCheckerCreator,
)
from ai.backend.manager.models.idle_checker.purgers import IdleCheckerAssignmentPurger
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.idle_checker.scopes import IdleCheckerAssignmentOperationScope
from ai.backend.manager.models.idle_checker.searchers import IdleCheckerAssignmentSearcher
from ai.backend.manager.models.idle_checker.updaters import (
    IdleCheckerAssignmentDisabler,
    IdleCheckerAssignmentEnabler,
)
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_group import ResourceGroupOpts, ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.testutils.db import with_tables


async def _provision(db_sess: sa.ext.asyncio.AsyncSession, scope: EntityIdentifier) -> None:
    """The node every scope needs before a relation can name it."""
    node = VirtualEntityRow(entity_type=scope.entity_type(), entity_id=scope)
    db_sess.add(node)
    await db_sess.flush()
    db_sess.add(EntityMembershipRow(virtual_entity_id=node.id, member_entity_id=node.id))
    db_sess.add(ScopeBindingRow(virtual_entity_id=node.id, scope_entity_id=node.id))
    await db_sess.flush()


async def _node_id(db_sess: sa.ext.asyncio.AsyncSession, entity: EntityIdentifier) -> uuid.UUID:
    node_id = await db_sess.scalar(
        sa.select(VirtualEntityRow.id).where(
            VirtualEntityRow.entity_type == entity.entity_type(),
            VirtualEntityRow.entity_id == entity,
        )
    )
    assert node_id is not None
    return uuid.UUID(str(node_id))


class TestIdleCheckerAssignmentRepository:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                EntityMembershipFieldRow,
                ScopeBindingRow,
                EntityLabelRow,
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                ProjectRow,
                UserRow,
                ResourceGroupRow,
                RoleRow,
                PermissionRow,
                IdleCheckerRow,
                IdleCheckerBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, database: ExtendedAsyncSAEngine) -> IdleCheckerRepository:
        return IdleCheckerRepository(DBOpsProvider(database), RelationOpsProvider(database))

    @pytest.fixture
    def relations(self, database: ExtendedAsyncSAEngine) -> RbacRelationRepository:
        return RbacRelationRepository(RelationOpsProvider(database))

    async def _link(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        creator: IdleCheckerAssignmentCreator,
        scope: EntityIdentifier,
        checker_id: IdleCheckerID,
    ) -> IdleCheckerAssignmentData:
        """Link the pair and read it back, as the adapter does."""
        await relations.create([(scope, checker_id)], creator)
        return await repository.get_assignment_by_pair(scope, checker_id)

    async def _add_domain(self, database: ExtendedAsyncSAEngine) -> DomainID:
        domain_id = DomainID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=f"domain-{domain_id.hex[:8]}",
                    total_resource_slots=ResourceSlot(),
                )
            )
            await _provision(db_sess, domain_id)
        return domain_id

    @pytest.fixture
    async def domain_id(self, database: ExtendedAsyncSAEngine) -> DomainID:
        return await self._add_domain(database)

    @pytest.fixture
    async def second_domain_id(self, database: ExtendedAsyncSAEngine) -> DomainID:
        return await self._add_domain(database)

    @pytest.fixture
    async def resource_group_id(self, database: ExtendedAsyncSAEngine) -> ResourceGroupID:
        resource_group_id = ResourceGroupID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            db_sess.add(
                ResourceGroupRow(
                    id=resource_group_id,
                    name=f"rg-{resource_group_id.hex[:8]}",
                    driver="test",
                    scheduler="test",
                    scheduler_opts=ResourceGroupOpts(),
                )
            )
            await _provision(db_sess, resource_group_id)
        return resource_group_id

    @pytest.fixture
    async def project_id(
        self,
        database: ExtendedAsyncSAEngine,
        domain_id: DomainID,
    ) -> ProjectID:
        project_id = ProjectID(uuid.uuid4())
        policy_name = f"prp-{project_id.hex[:8]}"
        async with database.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=0,
                )
            )
            await db_sess.flush()
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name=f"project-{project_id.hex[:8]}",
                    domain_name=f"domain-{domain_id.hex[:8]}",
                    total_resource_slots=ResourceSlot(),
                    resource_policy=policy_name,
                )
            )
            await _provision(db_sess, project_id)
        return project_id

    @pytest.fixture
    async def user_id(
        self,
        database: ExtendedAsyncSAEngine,
        domain_id: DomainID,
    ) -> UserID:
        user_id = UserID(uuid.uuid4())
        policy_name = f"urp-{user_id.hex[:8]}"
        async with database.begin_session() as db_sess:
            db_sess.add(
                UserResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=0,
                    max_customized_image_count=0,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username=f"user-{user_id.hex[:8]}",
                    email=f"{user_id.hex[:8]}@example.com",
                    password=None,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=f"domain-{domain_id.hex[:8]}",
                    role=UserRole.USER,
                    resource_policy=policy_name,
                    domain_id=domain_id,
                )
            )
            await _provision(db_sess, user_id)
        return user_id

    @pytest.fixture
    async def checker(self, database: ExtendedAsyncSAEngine) -> IdleCheckerData:
        """The target every binding names, created the way the catalog creates it so
        it has the node a relation needs."""
        ops: OpsRepository[IdleCheckerData] = OpsRepository(V2DBOpsProvider(database))
        return await ops.create_global_entity(
            IdleCheckerCreator(
                name="session lifetime",
                description=None,
                target_session_types=[SessionTypes.INTERACTIVE],
                initial_grace_period_seconds=30,
                spec=IdleCheckerSpec(
                    type=CheckerType.SESSION_LIFETIME,
                    session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
                ),
            )
        )

    @pytest.fixture
    async def domain_assignment(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_id: DomainID,
    ) -> IdleCheckerAssignmentData:
        return await self._link(
            relations, repository, IdleCheckerAssignmentCreator(enabled=True), domain_id, checker.id
        )

    async def test_create_links_the_scope_to_the_checker(
        self,
        relations: RbacRelationRepository,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        resource_group_id: ResourceGroupID,
    ) -> None:
        assignment = await self._link(
            relations,
            repository,
            IdleCheckerAssignmentCreator(enabled=False),
            resource_group_id,
            checker.id,
        )

        async with database.begin_readonly_session() as db_sess:
            scope_node = await _node_id(db_sess, resource_group_id)
            checker_node = await _node_id(db_sess, checker.id)
            binding_node = await db_sess.scalar(
                sa.select(VirtualEntityRow.id).where(VirtualEntityRow.entity_id == assignment.id)
            )
            govern = await db_sess.scalar(
                sa.select(ScopeBindingRow).where(
                    ScopeBindingRow.virtual_entity_id == checker_node,
                    ScopeBindingRow.scope_entity_id == scope_node,
                )
            )
            share = await db_sess.scalar(
                sa.select(EntityMembershipRow).where(
                    EntityMembershipRow.virtual_entity_id == checker_node,
                    EntityMembershipRow.member_entity_id == scope_node,
                )
            )

        assert assignment.scope_type is ScopeType.RESOURCE_GROUP
        assert assignment.scope_id == resource_group_id
        assert assignment.enabled is False
        # A relation makes no node of its own.
        assert binding_node is None
        # The scope governs the checker under READ; the checker reads the scope.
        assert govern is not None
        assert govern.permission_cap == Permission.READ
        assert share is not None
        assert share.capped is True

    async def test_linking_an_already_linked_pair_is_silent(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_id: DomainID,
        domain_assignment: IdleCheckerAssignmentData,
    ) -> None:
        linked = await relations.create(
            [(domain_id, checker.id)], IdleCheckerAssignmentCreator(enabled=False)
        )

        assert linked == [False]

    async def test_create_assignment_missing_checker_raises(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        domain_id: DomainID,
    ) -> None:
        with pytest.raises(IdleCheckerNotFound):
            await self._link(
                relations,
                repository,
                IdleCheckerAssignmentCreator(enabled=True),
                domain_id,
                IdleCheckerID(uuid.uuid4()),
            )

    async def test_create_assignment_missing_scope_raises(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
    ) -> None:
        with pytest.raises(IdleCheckerAssignmentScopeNotFound):
            await self._link(
                relations,
                repository,
                IdleCheckerAssignmentCreator(enabled=True),
                DomainID(uuid.uuid4()),
                checker.id,
            )

    async def test_create_assignment_on_unsupported_scope_raises(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
    ) -> None:
        with pytest.raises(IdleCheckerAssignmentScopeNotFound):
            await self._link(
                relations,
                repository,
                IdleCheckerAssignmentCreator(enabled=True),
                IdleCheckerID(uuid.uuid4()),
                checker.id,
            )

    async def test_create_assignment_on_user_scope(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        user_id: UserID,
    ) -> None:
        assignment = await self._link(
            relations, repository, IdleCheckerAssignmentCreator(enabled=True), user_id, checker.id
        )

        assert assignment.scope_type is ScopeType.USER
        assert assignment.scope_id == user_id

    async def test_create_assignment_on_project_scope(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        project_id: ProjectID,
    ) -> None:
        assignment = await self._link(
            relations,
            repository,
            IdleCheckerAssignmentCreator(enabled=True),
            project_id,
            checker.id,
        )

        assert assignment.scope_type is ScopeType.PROJECT
        assert assignment.scope_id == project_id

    async def test_disable_and_enable_switch_the_row_alone(
        self,
        relations: RbacRelationRepository,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_id: DomainID,
        domain_assignment: IdleCheckerAssignmentData,
    ) -> None:
        await relations.delete([(domain_id, checker.id)], IdleCheckerAssignmentDisabler())
        disabled = await repository.get_assignment_by_pair(domain_id, checker.id)
        async with database.begin_readonly_session() as db_sess:
            scope_node = await _node_id(db_sess, domain_id)
            checker_node = await _node_id(db_sess, checker.id)
            govern = await db_sess.scalar(
                sa.select(ScopeBindingRow).where(
                    ScopeBindingRow.virtual_entity_id == checker_node,
                    ScopeBindingRow.scope_entity_id == scope_node,
                )
            )
        await relations.restore([(domain_id, checker.id)], IdleCheckerAssignmentEnabler())
        enabled = await repository.get_assignment_by_pair(domain_id, checker.id)

        assert disabled.id == domain_assignment.id
        assert disabled.enabled is False
        # Switching off keeps what each side reads of the other.
        assert govern is not None
        assert enabled.enabled is True

    async def test_switching_a_pair_that_stands_in_no_relation_is_silent(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_id: DomainID,
    ) -> None:
        switched = await relations.delete(
            [(domain_id, checker.id)], IdleCheckerAssignmentDisabler()
        )

        assert switched == [False]

    async def test_purge_assignment_unlinks(
        self,
        relations: RbacRelationRepository,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_id: DomainID,
        domain_assignment: IdleCheckerAssignmentData,
    ) -> None:
        await relations.purge([(domain_id, checker.id)], IdleCheckerAssignmentPurger())

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(IdleCheckerBindingRow, domain_assignment.id)
            scope_node = await _node_id(db_sess, domain_id)
            checker_node = await _node_id(db_sess, checker.id)
            govern = await db_sess.scalar(
                sa.select(ScopeBindingRow).where(
                    ScopeBindingRow.virtual_entity_id == checker_node,
                    ScopeBindingRow.scope_entity_id == scope_node,
                )
            )

        assert row is None
        assert govern is None

    async def test_unlinking_an_unlinked_pair_is_silent(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_id: DomainID,
    ) -> None:
        unlinked = await relations.purge([(domain_id, checker.id)], IdleCheckerAssignmentPurger())

        assert unlinked == [False]

    async def test_get_assignment_by_id(
        self,
        repository: IdleCheckerRepository,
        domain_assignment: IdleCheckerAssignmentData,
    ) -> None:
        assert await repository.get_assignment(domain_assignment.id) == domain_assignment
        with pytest.raises(IdleCheckerAssignmentNotFound):
            await repository.get_assignment(IdleCheckerAssignmentID(uuid.uuid4()))

    async def test_admin_search_filters_by_enabled(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_assignment: IdleCheckerAssignmentData,
        resource_group_id: ResourceGroupID,
    ) -> None:
        disabled_assignment = await self._link(
            relations,
            repository,
            IdleCheckerAssignmentCreator(enabled=False),
            resource_group_id,
            checker.id,
        )

        result = await repository.admin_search_assignments(
            IdleCheckerAssignmentSearcher(
                conditions=[IdleCheckerAssignmentConditions.by_enabled_equals(False)],
                pagination=NoPagination(),
            )
        )

        assert result.items == [disabled_assignment]
        assert result.total_count == 1

    async def test_scoped_search_returns_only_assignments_in_scopes(
        self,
        relations: RbacRelationRepository,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_assignment: IdleCheckerAssignmentData,
        domain_id: DomainID,
        second_domain_id: DomainID,
        resource_group_id: ResourceGroupID,
        project_id: ProjectID,
    ) -> None:
        creator = IdleCheckerAssignmentCreator(enabled=True)
        second_domain_assignment = await self._link(
            relations, repository, creator, second_domain_id, checker.id
        )
        resource_group_assignment = await self._link(
            relations, repository, creator, resource_group_id, checker.id
        )
        project_assignment = await self._link(
            relations, repository, creator, project_id, checker.id
        )

        single_scope_result = await repository.scoped_search_assignments(
            [IdleCheckerAssignmentOperationScope(scope=domain_id)],
            IdleCheckerAssignmentSearcher(pagination=NoPagination()),
        )
        mixed_union_result = await repository.scoped_search_assignments(
            [
                IdleCheckerAssignmentOperationScope(scope=domain_id),
                IdleCheckerAssignmentOperationScope(scope=resource_group_id),
                IdleCheckerAssignmentOperationScope(scope=project_id),
            ],
            IdleCheckerAssignmentSearcher(pagination=NoPagination()),
        )

        # A single scope item excludes every other scope kind and id.
        assert single_scope_result.items == [domain_assignment]
        # Mixed scope kinds are OR'd; the unrequested second domain stays excluded.
        assert {assignment.id for assignment in mixed_union_result.items} == {
            domain_assignment.id,
            resource_group_assignment.id,
            project_assignment.id,
        }
        assert second_domain_assignment.id not in {
            assignment.id for assignment in mixed_union_result.items
        }

    async def test_scoped_search_with_empty_scopes_raises(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        with pytest.raises(EmptyOperationScopeError):
            await repository.scoped_search_assignments(
                [],
                IdleCheckerAssignmentSearcher(pagination=NoPagination()),
            )
