from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.types import ScopeType as VirtualScopeType
from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    NetworkTimeoutSpec,
    SessionLifetimeSpec,
)
from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.common.exception import BackendAIError, UserNotFound
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.errors.idle_checker import (
    IdleCheckerNotFound,
    IdleCheckerTypeChangeNotAllowed,
)
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.idle_checker.conditions import IdleCheckerConditions
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    NoPagination,
    Purger,
    Updater,
)
from ai.backend.manager.repositories.idle_checker.creators import IdleCheckerCreatorSpec
from ai.backend.manager.repositories.idle_checker.purgers import IdleCheckerPurgerSpec
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerSearchScope
from ai.backend.manager.repositories.idle_checker.updaters import IdleCheckerUpdaterSpec
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class OwnerScopes:
    user: ScopeRef
    project: ScopeRef


@dataclass(frozen=True)
class ScopedCheckers:
    user: IdleCheckerData
    project: IdleCheckerData


class TestIdleCheckerRepository:
    @pytest.fixture
    async def database(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VirtualScopeRow,
                EntityMembershipRow,
                ScopeBindingRow,
                AssociationScopesEntitiesRow,
                IdleCheckerRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, database: ExtendedAsyncSAEngine) -> IdleCheckerRepository:
        return IdleCheckerRepository(RBACOpsProvider(database))

    @pytest.fixture
    async def owner_scopes(self, database: ExtendedAsyncSAEngine) -> OwnerScopes:
        domain_name = f"idle-checker-{uuid.uuid4().hex[:8]}"
        user_policy_name = f"user-policy-{uuid.uuid4().hex[:8]}"
        project_policy_name = f"project-policy-{uuid.uuid4().hex[:8]}"
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        async with database.begin_session() as db_sess:
            db_sess.add_all([
                DomainRow(name=domain_name),
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=1024,
                    max_session_count_per_model_session=10,
                    max_customized_image_count=10,
                ),
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=1024,
                    max_network_count=10,
                ),
            ])
            await db_sess.flush()
            db_sess.add_all([
                UserRow(
                    uuid=user_id,
                    username=f"user-{user_id}",
                    email=f"{user_id}@example.com",
                    domain_name=domain_name,
                    resource_policy=user_policy_name,
                ),
                GroupRow(
                    id=project_id,
                    name=f"project-{project_id}",
                    domain_name=domain_name,
                    resource_policy=project_policy_name,
                ),
            ])
        return OwnerScopes(
            user=ScopeRef(VirtualScopeType(ScopeType.USER.value), user_id),
            project=ScopeRef(VirtualScopeType(ScopeType.PROJECT.value), project_id),
        )

    @pytest.fixture
    def creator_spec(self) -> IdleCheckerCreatorSpec:
        return IdleCheckerCreatorSpec(
            name="personal lifetime",
            description=None,
            checker_type=CheckerType.SESSION_LIFETIME,
            target_session_types=[SessionTypes.INTERACTIVE],
            initial_grace_period_seconds=30,
            spec=IdleCheckerSpec(
                type=CheckerType.SESSION_LIFETIME,
                session_lifetime=SessionLifetimeSpec(max_lifetime_seconds=3600),
            ),
        )

    @pytest.fixture
    async def created_checker(
        self,
        repository: IdleCheckerRepository,
        owner_scopes: OwnerScopes,
        creator_spec: IdleCheckerCreatorSpec,
    ) -> IdleCheckerData:
        return await repository.create(Creator(spec=creator_spec), owner_scopes.user)

    @pytest.fixture
    async def scoped_checkers(
        self,
        repository: IdleCheckerRepository,
        owner_scopes: OwnerScopes,
        creator_spec: IdleCheckerCreatorSpec,
    ) -> ScopedCheckers:
        return ScopedCheckers(
            user=await repository.create(Creator(spec=creator_spec), owner_scopes.user),
            project=await repository.create(Creator(spec=creator_spec), owner_scopes.project),
        )

    @pytest.mark.parametrize("owner_name", ["user", "project"])
    async def test_create_dual_writes_owner_relationship(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        owner_scopes: OwnerScopes,
        creator_spec: IdleCheckerCreatorSpec,
        owner_name: str,
    ) -> None:
        owner_scope = getattr(owner_scopes, owner_name)

        checker = await repository.create(Creator(spec=creator_spec), owner_scope)

        async with database.begin_readonly_session() as db_sess:
            association = (
                await db_sess.execute(
                    sa.select(AssociationScopesEntitiesRow).where(
                        AssociationScopesEntitiesRow.entity_type == EntityType.IDLE_CHECKER,
                        AssociationScopesEntitiesRow.entity_id == str(checker.id),
                    )
                )
            ).scalar_one()
            membership = (
                await db_sess.execute(
                    sa.select(EntityMembershipRow).where(
                        EntityMembershipRow.entity_type == EntityType.IDLE_CHECKER.value,
                        EntityMembershipRow.entity_id == checker.id,
                    )
                )
            ).scalar_one()
            virtual_scope = (
                await db_sess.execute(
                    sa.select(VirtualScopeRow).where(
                        VirtualScopeRow.scope_type == owner_scope.scope_type,
                        VirtualScopeRow.scope_id == owner_scope.scope_id,
                    )
                )
            ).scalar_one()

        assert checker.name == creator_spec.name
        assert checker.checker_type == creator_spec.checker_type
        assert association.scope_type.value == owner_scope.scope_type
        assert association.scope_id == str(owner_scope.scope_id)
        assert membership.virtual_scope_id == virtual_scope.id

    async def test_search_by_id_returns_checker(
        self,
        repository: IdleCheckerRepository,
        owner_scopes: OwnerScopes,
        created_checker: IdleCheckerData,
    ) -> None:
        result = await repository.search(
            BatchQuerier(
                conditions=[IdleCheckerConditions.by_ids([created_checker.id])],
                pagination=NoPagination(),
            ),
            [IdleCheckerSearchScope(owner_scopes.user)],
        )

        assert result.items == [created_checker]

    async def test_search_by_missing_id_returns_empty(
        self,
        repository: IdleCheckerRepository,
        owner_scopes: OwnerScopes,
    ) -> None:
        result = await repository.search(
            BatchQuerier(
                conditions=[IdleCheckerConditions.by_ids([IdleCheckerID(uuid.uuid4())])],
                pagination=NoPagination(),
            ),
            [IdleCheckerSearchScope(owner_scopes.user)],
        )

        assert result.items == []

    @pytest.mark.parametrize(
        ("scope_name", "checker_name"),
        [
            ("user", "user"),
            ("project", "project"),
        ],
    )
    async def test_search_returns_only_directly_owned_checkers(
        self,
        repository: IdleCheckerRepository,
        owner_scopes: OwnerScopes,
        scoped_checkers: ScopedCheckers,
        scope_name: str,
        checker_name: str,
    ) -> None:
        result = await repository.search(
            BatchQuerier(pagination=NoPagination()),
            [IdleCheckerSearchScope(getattr(owner_scopes, scope_name))],
        )

        assert result.items == [getattr(scoped_checkers, checker_name)]
        assert result.total_count == 1

    async def test_search_or_combines_owner_scopes(
        self,
        repository: IdleCheckerRepository,
        owner_scopes: OwnerScopes,
        scoped_checkers: ScopedCheckers,
    ) -> None:
        result = await repository.search(
            BatchQuerier(
                conditions=[
                    IdleCheckerConditions.by_ids([
                        scoped_checkers.user.id,
                        scoped_checkers.project.id,
                    ])
                ],
                pagination=NoPagination(),
            ),
            [
                IdleCheckerSearchScope(owner_scopes.user),
                IdleCheckerSearchScope(owner_scopes.project),
            ],
        )

        assert {checker.id for checker in result.items} == {
            scoped_checkers.user.id,
            scoped_checkers.project.id,
        }
        assert result.total_count == 2

    @pytest.mark.parametrize(
        ("scope_type", "expected_error"),
        [
            (ScopeType.USER, UserNotFound),
            (ScopeType.PROJECT, ProjectNotFound),
        ],
    )
    async def test_search_missing_owner_raises(
        self,
        repository: IdleCheckerRepository,
        scope_type: ScopeType,
        expected_error: type[BackendAIError],
    ) -> None:
        missing_scope = ScopeRef(VirtualScopeType(scope_type.value), uuid.uuid4())

        with pytest.raises(expected_error):
            await repository.search(
                BatchQuerier(pagination=NoPagination()),
                [IdleCheckerSearchScope(missing_scope)],
            )

    async def test_update_changes_mutable_fields(
        self,
        repository: IdleCheckerRepository,
        created_checker: IdleCheckerData,
    ) -> None:
        updated = await repository.update(
            Updater(
                spec=IdleCheckerUpdaterSpec(name=OptionalState.update("renamed lifetime")),
                pk_value=created_checker.id,
            )
        )

        assert updated.name == "renamed lifetime"

    async def test_rejects_checker_type_change(
        self,
        repository: IdleCheckerRepository,
        created_checker: IdleCheckerData,
    ) -> None:
        with pytest.raises(IdleCheckerTypeChangeNotAllowed):
            await repository.update(
                Updater(
                    spec=IdleCheckerUpdaterSpec(
                        spec=OptionalState.update(
                            IdleCheckerSpec(
                                type=CheckerType.NETWORK_TIMEOUT,
                                network=NetworkTimeoutSpec(),
                            )
                        )
                    ),
                    pk_value=created_checker.id,
                )
            )

    async def test_update_missing_checker_raises(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        with pytest.raises(IdleCheckerNotFound):
            await repository.update(
                Updater(
                    spec=IdleCheckerUpdaterSpec(name=OptionalState.update("renamed lifetime")),
                    pk_value=IdleCheckerID(uuid.uuid4()),
                )
            )

    async def test_purge_removes_checker_and_owner_relationships(
        self,
        database: ExtendedAsyncSAEngine,
        repository: IdleCheckerRepository,
        created_checker: IdleCheckerData,
    ) -> None:
        purged = await repository.purge(Purger(spec=IdleCheckerPurgerSpec(created_checker.id)))

        async with database.begin_readonly_session() as db_sess:
            checker = await db_sess.get(IdleCheckerRow, created_checker.id)
            association_count = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(
                    AssociationScopesEntitiesRow.entity_type == EntityType.IDLE_CHECKER,
                    AssociationScopesEntitiesRow.entity_id == str(created_checker.id),
                )
            )
            membership_count = await db_sess.scalar(
                sa.select(sa.func.count())
                .select_from(EntityMembershipRow)
                .where(
                    EntityMembershipRow.entity_type == EntityType.IDLE_CHECKER.value,
                    EntityMembershipRow.entity_id == created_checker.id,
                )
            )

        assert purged == created_checker
        assert checker is None
        assert association_count == 0
        assert membership_count == 0

    async def test_purge_missing_checker_raises(
        self,
        repository: IdleCheckerRepository,
    ) -> None:
        with pytest.raises(IdleCheckerNotFound):
            await repository.purge(Purger(spec=IdleCheckerPurgerSpec(IdleCheckerID(uuid.uuid4()))))
