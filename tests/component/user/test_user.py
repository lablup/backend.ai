from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.common.dto.manager.query import ArrayFilter, IntFilter, StringFilter
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserRequest,
    DeleteUserResponse,
    GetUserResponse,
    OrderDirection,
    PurgeUserRequest,
    PurgeUserResponse,
    SearchUsersRequest,
    SearchUsersResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    UserFilter,
    UserOrder,
    UserOrderField,
    UserRole,
    UserStatus,
)
from ai.backend.common.dto.manager.v2.user.request import (
    SearchUsersRequest as V2SearchUsersRequest,
)
from ai.backend.common.dto.manager.v2.user.request import (
    UserFilter as V2UserFilter,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    Permission,
    ScopeType,
)
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.user import users
from ai.backend.testutils.fixtures import DomainFixtureData

from .conftest import (
    ArrayMatchUsers,
    ScalarMatchUsers,
    SingleGidUsers,
    UserFactory,
)


class TestUserCreate:
    async def test_admin_creates_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await user_factory(
            email=f"new-{unique}@test.local",
            username=f"new-{unique}",
        )
        assert isinstance(result, CreateUserResponse)
        assert result.user.email == f"new-{unique}@test.local"
        assert result.user.username == f"new-{unique}"
        assert result.user.status == UserStatus.ACTIVE
        assert result.user.id is not None

    async def test_regular_user_cannot_create_user(
        self,
        user_registry: BackendAIClientRegistry,
        domain_fixture: DomainFixtureData,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        request = CreateUserRequest(
            email=f"denied-{unique}@test.local",
            username=f"denied-{unique}",
            password="test-password-1234",
            domain_name=domain_fixture.domain_name,
            resource_policy=resource_policy_fixture,
        )
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.create(request)

    async def test_create_user_with_optional_fields(
        self,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await user_factory(
            email=f"opts-{unique}@test.local",
            username=f"opts-{unique}",
            full_name="Full Name Test",
            description="A test user with optional fields",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )
        assert result.user.full_name == "Full Name Test"
        assert result.user.description == "A test user with optional fields"
        assert result.user.role == UserRole.USER


class TestUserGet:
    async def test_admin_gets_user_by_uuid(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        get_result = await admin_registry.user.get(target_user.user.id)
        assert isinstance(get_result, GetUserResponse)
        assert get_result.user.id == target_user.user.id
        assert get_result.user.email == target_user.user.email
        assert get_result.user.username == target_user.user.username

    async def test_regular_user_cannot_get_user(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.get(target_user.user.id)

    async def test_get_nonexistent_user_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.user.get(uuid.uuid4())


class TestUserSearch:
    async def test_admin_searches_users(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        await user_factory()
        await user_factory()
        result = await admin_registry.user.search(SearchUsersRequest())
        assert isinstance(result, SearchUsersResponse)
        assert result.pagination.total >= 2
        assert len(result.items) >= 2

    async def test_search_with_email_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"emailf-{unique}"
        await user_factory(email=f"{marker}@test.local", username=marker)
        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(email=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total == 1
        assert result.items[0].email == f"{marker}@test.local"

    async def test_search_with_status_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        r = await user_factory(
            email=f"statf-{unique}@test.local",
            username=f"statf-{unique}",
            status=UserStatus.INACTIVE,
        )
        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(contains=f"statf-{unique}"),
                ),
            )
        )
        assert result.pagination.total >= 1
        found = [u for u in result.items if u.id == r.user.id]
        assert len(found) == 1
        assert found[0].status == UserStatus.INACTIVE

    async def test_search_with_ordering(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique1 = secrets.token_hex(4)
        unique2 = secrets.token_hex(4)
        await user_factory(email=f"aaa-{unique1}@test.local", username=f"aaa-{unique1}")
        await user_factory(email=f"zzz-{unique2}@test.local", username=f"zzz-{unique2}")
        result = await admin_registry.user.search(
            SearchUsersRequest(
                order=[UserOrder(field=UserOrderField.EMAIL, direction=OrderDirection.DESC)],
            )
        )
        emails = [u.email for u in result.items]
        assert emails == sorted(emails, reverse=True)

    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.user.search(
            SearchUsersRequest(limit=1, offset=0),
        )
        assert result.pagination.limit == 1
        assert len(result.items) <= 1

    async def test_search_with_username_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        target = await user_factory(username=f"unamef-{unique}")
        await user_factory(username=f"other-{unique}")

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(username=StringFilter(equals=f"unamef-{unique}")),
            )
        )
        assert result.pagination.total == 1
        assert result.items[0].username == target.user.username

    async def test_search_with_role_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        user_role = await user_factory(
            email=f"rolef-{unique}@test.local",
            username=f"rolef-{unique}",
            role=UserRole.USER,
        )

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(contains=f"rolef-{unique}"),
                    role=[UserRole.USER],
                ),
            )
        )
        assert result.pagination.total >= 1
        found = [u for u in result.items if u.id == user_role.user.id]
        assert len(found) == 1
        assert found[0].role == UserRole.USER

    async def test_search_with_compound_filters(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"compf-{unique}"
        target = await user_factory(
            email=f"{marker}@test.local",
            username=marker,
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )
        await user_factory(
            email=f"{marker}-inactive@test.local",
            username=f"{marker}-inactive",
            status=UserStatus.INACTIVE,
        )

        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(contains=marker),
                    status=[UserStatus.ACTIVE],
                    role=[UserRole.USER],
                ),
            )
        )
        assert result.pagination.total >= 1
        user_ids = {u.id for u in result.items}
        assert target.user.id in user_ids
        for user in result.items:
            assert marker in user.email
            assert user.status == UserStatus.ACTIVE
            assert user.role == UserRole.USER

    async def test_search_with_empty_result(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(equals="nonexistent-xyz-999@test.local"),
                ),
            )
        )
        assert len(result.items) == 0
        assert result.pagination.total == 0

    async def test_regular_user_cannot_search_users(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.search(SearchUsersRequest())


class TestUserUpdate:
    async def test_admin_updates_user_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        unique = secrets.token_hex(4)
        update_result = await admin_registry.user.update(
            target_user.user.id,
            UpdateUserRequest(
                username=f"updated-{unique}",
                full_name="Updated Full Name",
                description="Updated description",
            ),
        )
        assert isinstance(update_result, UpdateUserResponse)
        assert update_result.user.username == f"updated-{unique}"
        assert update_result.user.full_name == "Updated Full Name"
        assert update_result.user.description == "Updated description"

    async def test_regular_user_cannot_update_user(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.update(
                target_user.user.id,
                UpdateUserRequest(full_name="Denied"),
            )


class TestUserDelete:
    async def test_admin_soft_deletes_user(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        delete_result = await admin_registry.user.delete(
            DeleteUserRequest(user_id=target_user.user.id)
        )
        assert isinstance(delete_result, DeleteUserResponse)
        assert delete_result.success is True

    async def test_regular_user_cannot_delete_user(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.delete(DeleteUserRequest(user_id=target_user.user.id))


@pytest.fixture()
async def user_with_rbac_rows(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
) -> AsyncIterator[tuple[uuid.UUID, str]]:
    """Insert a user along with the RBAC rows that the create flow would
    normally generate (a SYSTEM role at the user's scope, two scope-entity
    associations, and a scope-bound permission). The test then exercises
    purge against this fully-controlled state.
    """
    user_id = uuid.uuid4()
    scope_id = str(user_id)
    role_id = uuid.uuid4()
    unique = secrets.token_hex(4)
    email = f"rbac-purge-{unique}@test.local"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(users).values(
                uuid=str(user_id),
                username=f"rbac-purge-{unique}",
                email=email,
                password=PasswordInfo(
                    password=secrets.token_urlsafe(8),
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name=f"RBAC Purge {unique}",
                description="Test user for RBAC purge cleanup",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
                role=UserRole.USER,
            )
        )
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"user-{scope_id[:8]}",
                status=RoleStatus.ACTIVE,
            )
        )
        # Role registered in the user's own scope (the per-user SYSTEM role binding).
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__).values(
                scope_type=ScopeType.USER,
                scope_id=scope_id,
                entity_type=EntityType.ROLE,
                entity_id=str(role_id),
                relation_type=RelationType.AUTO,
            )
        )
        # User registered as an entity in the domain scope.
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__).values(
                scope_type=ScopeType.DOMAIN,
                scope_id=domain_fixture.domain_name,
                entity_type=EntityType.USER,
                entity_id=scope_id,
                relation_type=RelationType.AUTO,
            )
        )
        await conn.execute(
            sa.insert(PermissionRow.__table__).values(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=scope_id,
                entity_type=EntityType.USER,
                operation=OperationType.READ,
                permission=Permission.READ,
            )
        )

    yield user_id, scope_id

    async with db_engine.begin() as conn:
        # Permissions cascade-delete with the role; explicit delete is a safety net.
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(
            AssociationScopesEntitiesRow.__table__.delete().where(
                sa.or_(
                    AssociationScopesEntitiesRow.__table__.c.scope_id == scope_id,
                    AssociationScopesEntitiesRow.__table__.c.entity_id == scope_id,
                )
            )
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))
        await conn.execute(users.delete().where(users.c.uuid == str(user_id)))


class TestUserPurge:
    async def test_admin_purges_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        r = await user_factory()
        purge_result = await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))
        assert isinstance(purge_result, PurgeUserResponse)
        assert purge_result.success is True
        with pytest.raises(NotFoundError):
            await admin_registry.user.get(r.user.id)

    async def test_regular_user_cannot_purge_user(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.purge(PurgeUserRequest(user_id=target_user.user.id))

    async def test_admin_purge_cleans_up_rbac_rows(
        self,
        admin_registry: BackendAIClientRegistry,
        user_with_rbac_rows: tuple[uuid.UUID, str],
        db_engine: SAEngine,
    ) -> None:
        """Purge must remove scope-entity associations and scope-bound permissions
        for the user, so the per-user SYSTEM role does not end up with dangling
        scope references that resolve to NULL via GraphQL.
        """
        user_id, scope_id = user_with_rbac_rows

        await admin_registry.user.purge(PurgeUserRequest(user_id=user_id))

        async with db_engine.connect() as conn:
            ase_after = await conn.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(
                    sa.or_(
                        sa.and_(
                            AssociationScopesEntitiesRow.scope_type == RBACElementType.USER,
                            AssociationScopesEntitiesRow.scope_id == scope_id,
                        ),
                        sa.and_(
                            AssociationScopesEntitiesRow.entity_type == RBACElementType.USER,
                            AssociationScopesEntitiesRow.entity_id == scope_id,
                        ),
                    )
                )
            )
            permissions_after = await conn.scalar(
                sa.select(sa.func.count())
                .select_from(PermissionRow)
                .where(
                    PermissionRow.scope_type == RBACElementType.USER,
                    PermissionRow.scope_id == scope_id,
                )
            )
        assert ase_after == 0, "association_scopes_entities rows should be cleaned up after purge"
        assert permissions_after == 0, "scope-bound permissions should be cleaned up after purge"


class TestUserBulkOperations:
    """Bulk operation actions/services/repositories exist but REST API v2
    endpoints are not wired yet.  Fill in once UserClient bulk methods are added."""

    @pytest.mark.xfail(reason="UserClient.bulk_create not implemented yet")
    async def test_bulk_create_all_success(self) -> None:
        """Bulk create all success -> all users created, correct count."""
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason="UserClient.bulk_create not implemented yet")
    async def test_bulk_create_partial_failure_duplicate_email(self) -> None:
        """Bulk create partial failure (duplicate email) -> success + failure lists with indices."""
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason="UserClient.bulk_create not implemented yet")
    async def test_bulk_create_empty_list(self) -> None:
        """Bulk create empty list -> empty result (no error)."""
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason="UserClient.bulk_modify not implemented yet")
    async def test_bulk_modify_all_success(self) -> None:
        """Bulk modify all success -> all users updated."""
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason="UserClient.bulk_modify not implemented yet")
    async def test_bulk_modify_partial_failure_nonexistent_user(self) -> None:
        """Bulk modify partial failure (non-existent user) -> success + failure with indices."""
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason="UserClient.bulk_purge not implemented yet")
    async def test_bulk_purge_partial_failure(self) -> None:
        """Bulk purge partial failure (vfolder mount blocking) -> success + failure with indices."""
        pytest.fail("Not implemented")

    @pytest.mark.xfail(reason="UserClient bulk operations not implemented yet")
    async def test_failure_index_tracking(self) -> None:
        """Failure index tracking -> each failure has correct index and error message."""
        pytest.fail("Not implemented")


class TestV2UserContainerFilter:
    """Container UID/GID filtering via POST /v2/users/search (v2 API).

    Seeds users with distinct container_uid / container_main_gid / container_gids and
    asserts the search narrows results. This is the only layer that validates the
    PostgreSQL array operators (``@>`` / ``&&``) for container_gids against real rows.
    """

    async def test_filter_by_container_uid(
        self,
        admin_v2_registry: V2ClientRegistry,
        container_uid_users: ScalarMatchUsers,
    ) -> None:
        result = await admin_v2_registry.user.admin_search(
            V2SearchUsersRequest(
                filter=V2UserFilter(container_uid=IntFilter(equals=container_uid_users.value))
            )
        )

        ids = {item.id for item in result.items}
        assert container_uid_users.matching.user.id in ids
        assert container_uid_users.other.user.id not in ids

    async def test_filter_by_container_main_gid(
        self,
        admin_v2_registry: V2ClientRegistry,
        container_main_gid_users: ScalarMatchUsers,
    ) -> None:
        result = await admin_v2_registry.user.admin_search(
            V2SearchUsersRequest(
                filter=V2UserFilter(
                    container_main_gid=IntFilter(equals=container_main_gid_users.value)
                )
            )
        )

        ids = {item.id for item in result.items}
        assert container_main_gid_users.matching.user.id in ids
        assert container_main_gid_users.other.user.id not in ids

    async def test_filter_container_gids_any(
        self,
        admin_v2_registry: V2ClientRegistry,
        container_gids_any_users: ArrayMatchUsers,
    ) -> None:
        result = await admin_v2_registry.user.admin_search(
            V2SearchUsersRequest(
                filter=V2UserFilter(
                    container_gids=ArrayFilter[int].model_validate({
                        "contains_any": container_gids_any_users.query
                    })
                )
            )
        )

        ids = {item.id for item in result.items}
        assert container_gids_any_users.matching.user.id in ids
        assert container_gids_any_users.other.user.id not in ids

    async def test_filter_container_gids_all(
        self,
        admin_v2_registry: V2ClientRegistry,
        container_gids_all_users: ArrayMatchUsers,
    ) -> None:
        result = await admin_v2_registry.user.admin_search(
            V2SearchUsersRequest(
                filter=V2UserFilter(
                    container_gids=ArrayFilter[int].model_validate({
                        "contains_all": container_gids_all_users.query
                    })
                )
            )
        )

        ids = {item.id for item in result.items}
        assert container_gids_all_users.matching.user.id in ids
        assert container_gids_all_users.other.user.id not in ids

    async def test_filter_single_gid_across_main_gid_and_gids(
        self,
        admin_v2_registry: V2ClientRegistry,
        single_gid_users: SingleGidUsers,
    ) -> None:
        """A single gid matches users via container_main_gid OR container_gids.contains."""
        gid = single_gid_users.gid
        result = await admin_v2_registry.user.admin_search(
            V2SearchUsersRequest(
                filter=V2UserFilter(
                    OR=[
                        V2UserFilter(container_main_gid=IntFilter(equals=gid)),
                        V2UserFilter(
                            container_gids=ArrayFilter[int].model_validate({"contains": gid})
                        ),
                    ]
                )
            )
        )

        ids = {item.id for item in result.items}
        assert single_gid_users.via_main_gid.user.id in ids
        assert single_gid_users.via_gids.user.id in ids
        assert single_gid_users.unrelated.user.id not in ids
