from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.data.permission.types import (
    ScopeType,
)
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData, IdleCheckerData
from ai.backend.manager.errors.idle_checker import (
    IdleCheckerAssignmentAlreadyExists,
    IdleCheckerAssignmentNotFound,
    IdleCheckerAssignmentScopeNotFound,
    IdleCheckerNotFound,
)
from ai.backend.manager.errors.repository import EmptySearchScopeError
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.idle_checker.conditions import IdleCheckerAssignmentConditions
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    NoPagination,
    Updater,
)
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.idle_checker.creators import (
    IdleCheckerAssignmentCreatorSpec,
    IdleCheckerCreatorSpec,
)
from ai.backend.manager.repositories.idle_checker.purgers import IdleCheckerAssignmentPurgerSpec
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerAssignmentSearchScope
from ai.backend.manager.repositories.idle_checker.updaters import IdleCheckerAssignmentUpdaterSpec
from ai.backend.manager.repositories.ops import DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


class TestIdleCheckerAssignmentRepository:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                GroupRow,
                ScalingGroupRow,
                RoleRow,
                PermissionRow,
                AssociationScopesEntitiesRow,
                IdleCheckerRow,
                IdleCheckerBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, database: ExtendedAsyncSAEngine) -> IdleCheckerRepository:
        return IdleCheckerRepository(DBOpsProvider(database))

    @pytest.fixture
    async def domain_id(self, database: ExtendedAsyncSAEngine) -> DomainID:
        domain_id = DomainID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=f"domain-{domain_id.hex[:8]}",
                    total_resource_slots=ResourceSlot(),
                )
            )
        return domain_id

    @pytest.fixture
    async def second_domain_id(self, database: ExtendedAsyncSAEngine) -> DomainID:
        domain_id = DomainID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=f"domain-{domain_id.hex[:8]}",
                    total_resource_slots=ResourceSlot(),
                )
            )
        return domain_id

    @pytest.fixture
    async def resource_group_id(self, database: ExtendedAsyncSAEngine) -> ResourceGroupID:
        resource_group_id = ResourceGroupID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    id=resource_group_id,
                    name=f"rg-{resource_group_id.hex[:8]}",
                    driver="test",
                    scheduler="test",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
        return resource_group_id

    @pytest.fixture
    async def project_id(
        self,
        database: ExtendedAsyncSAEngine,
        domain_id: DomainID,
    ) -> uuid.UUID:
        project_id = uuid.uuid4()
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
                GroupRow(
                    id=project_id,
                    name=f"project-{project_id.hex[:8]}",
                    domain_name=f"domain-{domain_id.hex[:8]}",
                    total_resource_slots=ResourceSlot(),
                    resource_policy=policy_name,
                )
            )
        return project_id

    @pytest.fixture
    async def checker(self, repository: IdleCheckerRepository) -> IdleCheckerData:
        return await repository.create(
            Creator(
                spec=IdleCheckerCreatorSpec(
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
        )

    @pytest.fixture
    async def domain_assignment(
        self,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_id: DomainID,
    ) -> IdleCheckerAssignmentData:
        return await repository.create_assignment(
            IdleCheckerAssignmentCreatorSpec(
                scope_type=ScopeType.DOMAIN,
                scope_id=domain_id,
                idle_checker_id=checker.id,
                enabled=True,
            )
        )

    async def test_create_assignment_on_resource_group_scope(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        resource_group_id: ResourceGroupID,
    ) -> None:
        assignment = await repository.create_assignment(
            IdleCheckerAssignmentCreatorSpec(
                scope_type=ScopeType.RESOURCE_GROUP,
                scope_id=resource_group_id,
                idle_checker_id=checker.id,
                enabled=False,
            )
        )

        async with database.begin_readonly_session() as db_sess:
            association_count = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_id == str(assignment.id))
            )

        assert assignment.scope_type is ScopeType.RESOURCE_GROUP
        assert assignment.scope_id == resource_group_id
        assert assignment.enabled is False
        # Create registers the assignment under its scope for RBAC scope-chain resolution.
        assert association_count == 1

    async def test_create_duplicate_assignment_raises(
        self,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_id: DomainID,
        domain_assignment: IdleCheckerAssignmentData,
    ) -> None:
        with pytest.raises(IdleCheckerAssignmentAlreadyExists):
            await repository.create_assignment(
                IdleCheckerAssignmentCreatorSpec(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=domain_id,
                    idle_checker_id=checker.id,
                    enabled=False,
                )
            )

    async def test_create_assignment_missing_checker_raises(
        self,
        repository: IdleCheckerRepository,
        domain_id: DomainID,
    ) -> None:
        with pytest.raises(IdleCheckerNotFound):
            await repository.create_assignment(
                IdleCheckerAssignmentCreatorSpec(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=domain_id,
                    idle_checker_id=IdleCheckerID(uuid.uuid4()),
                    enabled=True,
                )
            )

    async def test_create_assignment_missing_scope_raises(
        self,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
    ) -> None:
        with pytest.raises(IdleCheckerAssignmentScopeNotFound):
            await repository.create_assignment(
                IdleCheckerAssignmentCreatorSpec(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=uuid.uuid4(),
                    idle_checker_id=checker.id,
                    enabled=True,
                )
            )

    async def test_update_assignment_enabled(
        self,
        repository: IdleCheckerRepository,
        domain_assignment: IdleCheckerAssignmentData,
    ) -> None:
        updated = await repository.update_assignment(
            Updater(
                spec=IdleCheckerAssignmentUpdaterSpec(enabled=OptionalState.update(True)),
                pk_value=domain_assignment.id,
            )
        )

        assert updated.id == domain_assignment.id
        assert updated.enabled is True

    async def test_update_missing_assignment_raises(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        with pytest.raises(IdleCheckerAssignmentNotFound):
            await repository.update_assignment(
                Updater(
                    spec=IdleCheckerAssignmentUpdaterSpec(enabled=OptionalState.update(False)),
                    pk_value=IdleCheckerAssignmentID(uuid.uuid4()),
                )
            )

    async def test_purge_assignment_removes_row(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        domain_assignment: IdleCheckerAssignmentData,
    ) -> None:
        purged = await repository.purge_assignment(
            RBACEntityPurger(
                spec=IdleCheckerAssignmentPurgerSpec(assignment_id=domain_assignment.id)
            )
        )

        async with database.begin_readonly_session() as db_sess:
            row = await db_sess.get(IdleCheckerBindingRow, domain_assignment.id)
            association_count = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(AssociationScopesEntitiesRow.entity_id == str(domain_assignment.id))
            )

        assert purged == domain_assignment
        assert row is None
        # Purge also removes the RBAC scope association.
        assert association_count == 0

    async def test_purge_missing_assignment_raises(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        with pytest.raises(IdleCheckerAssignmentNotFound):
            await repository.purge_assignment(
                RBACEntityPurger(
                    spec=IdleCheckerAssignmentPurgerSpec(
                        assignment_id=IdleCheckerAssignmentID(uuid.uuid4())
                    )
                )
            )

    async def test_admin_search_filters_by_enabled(
        self,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_assignment: IdleCheckerAssignmentData,
        resource_group_id: ResourceGroupID,
    ) -> None:
        disabled_assignment = await repository.create_assignment(
            IdleCheckerAssignmentCreatorSpec(
                scope_type=ScopeType.RESOURCE_GROUP,
                scope_id=resource_group_id,
                idle_checker_id=checker.id,
                enabled=False,
            )
        )

        result = await repository.admin_search_assignments(
            BatchQuerier(
                conditions=[IdleCheckerAssignmentConditions.by_enabled_equals(False)],
                pagination=NoPagination(),
            )
        )

        assert result.items == [disabled_assignment]
        assert result.total_count == 1

    async def test_scoped_search_returns_only_assignments_in_scopes(
        self,
        repository: IdleCheckerRepository,
        checker: IdleCheckerData,
        domain_assignment: IdleCheckerAssignmentData,
        domain_id: DomainID,
        second_domain_id: DomainID,
        resource_group_id: ResourceGroupID,
        project_id: uuid.UUID,
    ) -> None:
        second_domain_assignment = await repository.create_assignment(
            IdleCheckerAssignmentCreatorSpec(
                scope_type=ScopeType.DOMAIN,
                scope_id=second_domain_id,
                idle_checker_id=checker.id,
                enabled=True,
            )
        )
        resource_group_assignment = await repository.create_assignment(
            IdleCheckerAssignmentCreatorSpec(
                scope_type=ScopeType.RESOURCE_GROUP,
                scope_id=resource_group_id,
                idle_checker_id=checker.id,
                enabled=True,
            )
        )
        project_assignment = await repository.create_assignment(
            IdleCheckerAssignmentCreatorSpec(
                scope_type=ScopeType.PROJECT,
                scope_id=project_id,
                idle_checker_id=checker.id,
                enabled=True,
            )
        )

        single_scope_result = await repository.scoped_search_assignments(
            BatchQuerier(pagination=NoPagination()),
            [IdleCheckerAssignmentSearchScope(scope_type=ScopeType.DOMAIN, scope_id=domain_id)],
        )
        mixed_union_result = await repository.scoped_search_assignments(
            BatchQuerier(pagination=NoPagination()),
            [
                IdleCheckerAssignmentSearchScope(scope_type=ScopeType.DOMAIN, scope_id=domain_id),
                IdleCheckerAssignmentSearchScope(
                    scope_type=ScopeType.RESOURCE_GROUP, scope_id=resource_group_id
                ),
                IdleCheckerAssignmentSearchScope(scope_type=ScopeType.PROJECT, scope_id=project_id),
            ],
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
        with pytest.raises(EmptySearchScopeError):
            await repository.scoped_search_assignments(
                BatchQuerier(pagination=NoPagination()),
                [],
            )
