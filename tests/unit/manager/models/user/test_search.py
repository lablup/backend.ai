"""Tests for the user search declarations and the deprecated cross-entity ones."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.domain.searchable_fields import DomainSearchableFields
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.keypair.searchable_fields import KeyPairSearchableFields
from ai.backend.manager.models.project import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.project.searchable_fields import ProjectSearchableFields
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.user.deprecated_search import (
    DeprecatedUserConditions,
    DeprecatedUserOrders,
)
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields
from ai.backend.manager.models.user.searchers import UserSearcher
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.user.db_source import UserDBSource
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.testutils.db import TableOrORM, with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

# Row imports above ensure mapper initialization (FK dependency order).
_WITH_TABLES: list[TableOrORM] = [
    DomainRow,
    ResourceGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    RoleRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    AssocGroupUserRow,
    ContainerRegistryRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    ReplicaGroupRow,
    RoutingRow,
    ResourcePresetRow,
    VirtualEntityRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    ScopeBindingRow,
]


class TestUserOwnFieldFilters:
    """The declared filters compile against the column, not the API field name."""

    def test_integration_name_filters_the_integration_id_column(self) -> None:
        spec = StringMatchSpec(value="ext-abc", case_insensitive=False, negated=False)
        condition = UserSearchableFields.own.integration_name.filter.contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "integration_id" in sql
        assert "LIKE" in sql.upper()
        assert "%ext-abc%" in sql

    def test_integration_name_case_insensitive_lowers_both_sides(self) -> None:
        spec = StringMatchSpec(value="ext-abc", case_insensitive=True, negated=False)
        condition = UserSearchableFields.own.integration_name.filter.contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "lower" in sql.lower()

    def test_integration_name_negated_inverts_the_match(self) -> None:
        spec = StringMatchSpec(value="ext-abc", case_insensitive=False, negated=True)
        condition = UserSearchableFields.own.integration_name.filter.contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "NOT LIKE" in sql.upper()

    def test_modified_at_filters_the_updated_at_column(self) -> None:
        condition = UserSearchableFields.own.modified_at.filter.after(
            datetime(2026, 1, 1, tzinfo=UTC)
        )
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "updated_at" in sql

    def test_two_conditions_off_one_field_stay_independent(self) -> None:
        conditions = UserSearchableFields.own.integration_name.filter
        spec_a = StringMatchSpec(value="alpha", case_insensitive=False, negated=False)
        spec_b = StringMatchSpec(value="beta", case_insensitive=False, negated=False)
        sql_a = str(conditions.contains(spec_a)().compile(compile_kwargs={"literal_binds": True}))
        sql_b = str(conditions.contains(spec_b)().compile(compile_kwargs={"literal_binds": True}))
        assert "alpha" in sql_a
        assert "beta" in sql_b


class TestUserContainerGidsFilters:
    """``container_gids`` is an array: containment only, and no order."""

    def test_contains_uses_the_containment_operator(self) -> None:
        condition = UserSearchableFields.own.container_gids.filter.contains(1000)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "container_gids" in sql
        assert "@>" in sql

    def test_contains_all_compares_against_every_value(self) -> None:
        condition = UserSearchableFields.own.container_gids.filter.contains_all([1000, 1001])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "@>" in sql
        assert "1000" in sql
        assert "1001" in sql

    def test_contains_any_uses_the_overlap_operator(self) -> None:
        condition = UserSearchableFields.own.container_gids.filter.contains_any([1000, 1001])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "&&" in sql

    def test_no_order_is_declared(self) -> None:
        assert UserSearchableFields.own.container_gids.order is None


class TestUserSensitiveFields:
    """An access control setting is neither filtered nor ordered by."""

    def test_allowed_client_ip_declares_neither_slot(self) -> None:
        field = UserSearchableFields.own.allowed_client_ip
        assert field.filter is None
        assert field.order is None


class TestKeyPairOwnFields:
    """The keypair declaration a user search reads its nested conditions from."""

    def test_secret_key_declares_neither_slot(self) -> None:
        field = KeyPairSearchableFields.own.secret_key
        assert field.filter is None
        assert field.order is None

    def test_ssh_private_key_declares_neither_slot(self) -> None:
        field = KeyPairSearchableFields.own.ssh_private_key
        assert field.filter is None
        assert field.order is None

    def test_access_key_is_open(self) -> None:
        field = KeyPairSearchableFields.own.access_key
        assert field.filter is not None
        assert field.order is not None

    def test_resource_policy_name_filters_the_resource_policy_column(self) -> None:
        spec = StringMatchSpec(value="default", case_insensitive=False, negated=False)
        condition = KeyPairSearchableFields.own.resource_policy_name.filter.equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "resource_policy" in sql


class TestUserNestedKeypairs:
    """The keypairs a user owns, reached from the user row."""

    def test_some_builds_an_exists_over_the_keypairs(self) -> None:
        correlation = UserSearchableFields.nested.keypairs.correlation
        condition = correlation.some([KeyPairSearchableFields.own.is_active.filter.equals(True)])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "keypairs" in sql
        assert "is_active" in sql

    def test_none_negates_the_exists(self) -> None:
        correlation = UserSearchableFields.nested.keypairs.correlation
        condition = correlation.none([KeyPairSearchableFields.own.is_active.filter.equals(True)])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "NOT (EXISTS" in sql

    def test_conditions_land_in_one_exists(self) -> None:
        correlation = UserSearchableFields.nested.keypairs.correlation
        condition = correlation.some([
            KeyPairSearchableFields.own.is_active.filter.equals(True),
            KeyPairSearchableFields.own.is_admin.filter.equals(False),
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert sql.count("EXISTS") == 1


class TestDeprecatedUserConditions:
    """The cross-entity filters kept working until they are removed."""

    def test_exists_domain_combined_single_exists(self) -> None:
        def cond_is_active() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.is_active == True  # noqa: E712

        def cond_desc_like() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.description.like("%test%")

        conditions: list[QueryCondition] = [cond_is_active, cond_desc_like]
        combined = DeprecatedUserConditions.exists_domain_combined(conditions)
        sql = str(combined().compile(compile_kwargs={"literal_binds": True}))
        assert sql.count("EXISTS") == 1
        assert "domains" in sql

    def test_exists_project_combined_reads_the_graph_membership(self) -> None:
        def cond_is_active() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectRow.is_active == True  # noqa: E712

        def cond_name_like() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectRow.name.like("%test%")

        conditions: list[QueryCondition] = [cond_is_active, cond_name_like]
        combined = DeprecatedUserConditions.exists_project_combined(conditions)
        sql = str(combined().compile(compile_kwargs={"literal_binds": True}))
        assert "entity_memberships" in sql
        assert "association_groups_users" not in sql

    def test_exists_project_combined_with_no_condition_still_compiles(self) -> None:
        combined = DeprecatedUserConditions.exists_project_combined([])
        assert isinstance(combined(), sa.sql.expression.ColumnElement)


class TestDeprecatedUserOrders:
    """The project order folds the user's projects with MIN."""

    def test_by_project_name_ascending(self) -> None:
        order = DeprecatedUserOrders.by_project_name(ascending=True)
        assert "ASC" in str(order).upper()

    def test_by_project_name_descending(self) -> None:
        order = DeprecatedUserOrders.by_project_name(ascending=False)
        assert "DESC" in str(order).upper()

    def test_by_project_name_aggregates_over_the_graph_membership(self) -> None:
        order = DeprecatedUserOrders.by_project_name(ascending=True)
        sql = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "min" in sql.lower()
        assert "entity_memberships" in sql
        assert "association_groups_users" not in sql
        assert "groups" in sql


# ==================== DB Integration Tests ====================


def _test_password_info() -> PasswordInfo:
    return PasswordInfo(
        password="test_password",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


@dataclass
class UserSearchFixture:
    active_domain: str
    inactive_domain: str
    user_in_active_domain: uuid.UUID
    user_in_inactive_domain: uuid.UUID
    project_alpha_id: uuid.UUID
    project_beta_id: uuid.UUID


class TestUserNestedSearchIntegration:
    """DB integration tests: nested filter/order applied via UserDBSource.search_users."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, _WITH_TABLES):
            yield database_connection

    @pytest.fixture
    async def user_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> UserDBSource:
        return UserDBSource(
            db=db_with_cleanup,
            v2_ops_provider=V2DBOpsProvider(db_with_cleanup),
            share_ops_provider=ShareOpsProvider(db_with_cleanup),
            policy_ops_provider=ResourcePolicyOpsProvider(db_with_cleanup),
            key_provider_pool=KeyProviderPool(
                providers=[], write_provider_type=KeyProviderType.PLAIN
            ),
        )

    @pytest.fixture
    async def search_fixture(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> UserSearchFixture:
        """Create two domains, two users, two projects, and M:N associations.

        - active_domain (is_active=True, desc="Research lab")
          - user_in_active_domain
          - project_alpha (user is member)
        - inactive_domain (is_active=False, desc="Archived department")
          - user_in_inactive_domain
          - project_beta (user is member)
        """
        domain_id = DomainID(uuid.uuid4())
        active_domain = f"active-dom-{uuid.uuid4().hex[:8]}"
        inactive_domain = f"inactive-dom-{uuid.uuid4().hex[:8]}"
        user_active_uuid = uuid.uuid4()
        user_inactive_uuid = uuid.uuid4()
        project_alpha_id = uuid.uuid4()
        project_beta_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as session:
            # Domains
            for dn, active, desc in [
                (active_domain, True, "Research lab"),
                (inactive_domain, False, "Archived department"),
            ]:
                domain_id = DomainID(uuid.uuid4())
                session.add(
                    DomainRow(
                        id=domain_id,
                        name=dn,
                        description=desc,
                        is_active=active,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts=VFolderHostPermissionMap(),
                        allowed_docker_registries=[],
                        dotfiles=b"",
                        integration_id=None,
                    )
                )
            await session.flush()

            # Resource policies
            urp = UserResourcePolicyRow(
                name=f"urp-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(urp)

            prp = ProjectResourcePolicyRow(
                name=f"prp-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(prp)
            await session.flush()

            # Users
            for uid, dom in [
                (user_active_uuid, active_domain),
                (user_inactive_uuid, inactive_domain),
            ]:
                session.add(
                    UserRow(
                        uuid=uid,
                        username=f"user-{uid.hex[:8]}",
                        email=f"user-{uid.hex[:8]}@test.io",
                        password=_test_password_info(),
                        need_password_change=False,
                        full_name="Test User",
                        description="",
                        status=UserStatus.ACTIVE,
                        status_info="active",
                        domain_name=dom,
                        role=UserRole.USER,
                        resource_policy=urp.name,
                        domain_id=domain_id,
                    )
                )
            await session.flush()

            # Projects
            for pid, pname, dom in [
                (project_alpha_id, "alpha-project", active_domain),
                (project_beta_id, "beta-project", inactive_domain),
            ]:
                session.add(
                    ProjectRow(
                        id=pid,
                        name=pname,
                        description="",
                        is_active=True,
                        domain_name=dom,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts=VFolderHostPermissionMap(),
                        integration_id=None,
                        resource_policy=prp.name,
                        type=ProjectType.GENERAL,
                    )
                )
            await session.flush()

            for uid, pid in [
                (user_active_uuid, project_alpha_id),
                (user_inactive_uuid, project_beta_id),
            ]:
                await VirtualEntitySeeder().enroll_user_in_project(session, pid, uid)

            await session.commit()

        return UserSearchFixture(
            active_domain=active_domain,
            inactive_domain=inactive_domain,
            user_in_active_domain=user_active_uuid,
            user_in_inactive_domain=user_inactive_uuid,
            project_alpha_id=project_alpha_id,
            project_beta_id=project_beta_id,
        )

    # ---- Domain nested filter tests ----

    async def test_search_users_with_domain_is_active_filter(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """The domain filter returns only the users in an active domain."""
        searcher = UserSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedUserConditions.exists_domain_combined([
                    DomainSearchableFields.own.is_active.filter.equals(True)
                ])
            ],
            orders=[],
        )
        result = await user_db_source.search_users(searcher)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_active_domain

    async def test_search_users_with_domain_description_contains_filter(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """search_users with domain description filter returns matching users."""
        spec = StringMatchSpec(value="Research", case_insensitive=True, negated=False)
        searcher = UserSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedUserConditions.exists_domain_combined([
                    DomainSearchableFields.own.description.filter.contains(spec)
                ])
            ],
            orders=[],
        )
        result = await user_db_source.search_users(searcher)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_active_domain

    # ---- Project nested filter tests ----

    async def test_search_users_with_project_name_contains_filter(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """search_users with by_project_name_contains filters by project membership."""
        spec = StringMatchSpec(value="alpha", case_insensitive=False, negated=False)
        searcher = UserSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedUserConditions.exists_project_combined([
                    ProjectSearchableFields.own.name.filter.contains(spec)
                ])
            ],
            orders=[],
        )
        result = await user_db_source.search_users(searcher)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_active_domain

    async def test_search_users_with_project_name_negated_filter(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """Negated project name filter excludes matching users."""
        spec = StringMatchSpec(value="alpha", case_insensitive=False, negated=True)
        searcher = UserSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedUserConditions.exists_project_combined([
                    ProjectSearchableFields.own.name.filter.contains(spec)
                ])
            ],
            orders=[],
        )
        result = await user_db_source.search_users(searcher)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_inactive_domain

    async def test_search_users_ignores_legacy_only_project_membership(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """A membership left only in the legacy association table does not match."""
        async with db_with_cleanup.begin_session() as session:
            session.add(
                AssocGroupUserRow(
                    user_id=search_fixture.user_in_inactive_domain,
                    group_id=search_fixture.project_alpha_id,
                )
            )
        spec = StringMatchSpec(value="alpha", case_insensitive=False, negated=False)
        searcher = UserSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedUserConditions.exists_project_combined([
                    ProjectSearchableFields.own.name.filter.contains(spec)
                ])
            ],
            orders=[],
        )
        result = await user_db_source.search_users(searcher)

        assert [item.uuid for item in result.items] == [search_fixture.user_in_active_domain]

    # ---- Domain nested order tests ----

    async def test_search_users_ordered_by_domain_name(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """The declared order sorts by the user's own domain_name column."""
        searcher = UserSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[UserSearchableFields.own.domain_name.order.apply(True)],
        )
        result = await user_db_source.search_users(searcher)

        assert result.total_count == 2
        # Sorted by domain name ascending: active-dom < inactive-dom
        assert result.items[0].uuid == search_fixture.user_in_active_domain
        assert result.items[1].uuid == search_fixture.user_in_inactive_domain

    # ---- Project nested order tests ----

    async def test_search_users_ordered_by_project_name(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """search_users with by_project_name order sorts by MIN(project name)."""
        searcher = UserSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[DeprecatedUserOrders.by_project_name(ascending=True)],
        )
        result = await user_db_source.search_users(searcher)

        assert result.total_count == 2
        # alpha-project < beta-project
        assert result.items[0].uuid == search_fixture.user_in_active_domain
        assert result.items[1].uuid == search_fixture.user_in_inactive_domain

    # ---- Combined filter + order tests ----

    async def test_search_users_combined_domain_filter_and_project_order(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """Combining domain filter + project order in single search call."""
        searcher = UserSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedUserConditions.exists_domain_combined([
                    DomainSearchableFields.own.is_active.filter.equals(True)
                ])
            ],
            orders=[DeprecatedUserOrders.by_project_name(ascending=True)],
        )
        result = await user_db_source.search_users(searcher)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_active_domain
