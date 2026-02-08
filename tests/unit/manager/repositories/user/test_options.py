"""Tests for UserConditions and UserOrders nested filter/order helpers."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination, QueryCondition
from ai.backend.manager.repositories.user.db_source import UserDBSource
from ai.backend.manager.repositories.user.options import (
    UserConditions,
    UserOrders,
)
from ai.backend.testutils.db import with_tables

# Row imports above ensure mapper initialization (FK dependency order).
_WITH_TABLES = [
    DomainRow,
    ScalingGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    GroupRow,
    AssocGroupUserRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    RoutingRow,
    ResourcePresetRow,
]


class TestUserConditionsDomainNestedFilters:
    """Tests for Domain nested filter conditions in UserConditions."""

    def test_by_domain_description_contains_generates_exists(self) -> None:
        spec = StringMatchSpec(value="research", case_insensitive=False, negated=False)
        condition = UserConditions.by_domain_description_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "domains" in sql

    def test_by_domain_description_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="research", case_insensitive=True, negated=False)
        condition = UserConditions.by_domain_description_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql

    def test_by_domain_description_contains_negated(self) -> None:
        spec = StringMatchSpec(value="research", case_insensitive=False, negated=True)
        condition = UserConditions.by_domain_description_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "NOT LIKE" in sql.upper()

    def test_by_domain_description_equals_generates_exists(self) -> None:
        spec = StringMatchSpec(value="exact", case_insensitive=False, negated=False)
        condition = UserConditions.by_domain_description_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "domains" in sql

    def test_by_domain_description_equals_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="Exact", case_insensitive=True, negated=False)
        condition = UserConditions.by_domain_description_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "lower" in sql

    def test_by_domain_description_equals_negated(self) -> None:
        spec = StringMatchSpec(value="exact", case_insensitive=False, negated=True)
        condition = UserConditions.by_domain_description_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        # sa.not_(col == val) compiles as col != val
        assert "!=" in sql or "NOT" in sql.upper()

    def test_by_domain_is_active(self) -> None:
        condition = UserConditions.by_domain_is_active(True)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "is_active" in sql

    def test_closure_independence(self) -> None:
        spec_a = StringMatchSpec(value="alpha", case_insensitive=False, negated=False)
        spec_b = StringMatchSpec(value="beta", case_insensitive=False, negated=False)
        cond_a = UserConditions.by_domain_description_contains(spec_a)
        cond_b = UserConditions.by_domain_description_contains(spec_b)
        sql_a = str(cond_a().compile(compile_kwargs={"literal_binds": True}))
        sql_b = str(cond_b().compile(compile_kwargs={"literal_binds": True}))
        assert sql_a != sql_b
        assert "alpha" in sql_a
        assert "beta" in sql_b

    def test_exists_domain_combined_single_exists(self) -> None:
        """Combined helper wraps raw column conditions into single EXISTS."""

        def cond_is_active() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.is_active == True  # noqa: E712

        def cond_desc_like() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.description.like("%test%")

        conditions: list[QueryCondition] = [cond_is_active, cond_desc_like]
        combined = UserConditions.exists_domain_combined(conditions)
        sql = str(combined().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert sql.count("EXISTS") == 1


class TestUserConditionsProjectNestedFilters:
    """Tests for Project (M:N) nested filter conditions in UserConditions."""

    def test_by_project_name_contains_generates_exists_with_join(self) -> None:
        spec = StringMatchSpec(value="ml-team", case_insensitive=False, negated=False)
        condition = UserConditions.by_project_name_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "association_groups_users" in sql
        assert "groups" in sql

    def test_by_project_name_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="ml-team", case_insensitive=True, negated=False)
        condition = UserConditions.by_project_name_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql

    def test_by_project_name_contains_negated(self) -> None:
        spec = StringMatchSpec(value="ml-team", case_insensitive=False, negated=True)
        condition = UserConditions.by_project_name_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "NOT LIKE" in sql.upper()

    def test_by_project_name_equals_generates_exists(self) -> None:
        spec = StringMatchSpec(value="project-a", case_insensitive=False, negated=False)
        condition = UserConditions.by_project_name_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "association_groups_users" in sql

    def test_by_project_name_equals_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="Project-A", case_insensitive=True, negated=False)
        condition = UserConditions.by_project_name_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "lower" in sql

    def test_by_project_is_active(self) -> None:
        condition = UserConditions.by_project_is_active(True)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "is_active" in sql
        assert "association_groups_users" in sql

    def test_exists_project_combined_single_exists(self) -> None:
        """Combined helper wraps raw column conditions into single EXISTS."""

        def cond_is_active() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.is_active == True  # noqa: E712

        def cond_name_like() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.name.like("%test%")

        conditions: list[QueryCondition] = [cond_is_active, cond_name_like]
        combined = UserConditions.exists_project_combined(conditions)
        sql = str(combined().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert sql.count("EXISTS") == 1
        assert "association_groups_users" in sql

    def test_exists_project_combined_returns_column_element(self) -> None:
        conditions: list[QueryCondition] = []
        combined = UserConditions.exists_project_combined(conditions)
        result = combined()
        assert isinstance(result, sa.sql.expression.ColumnElement)

    def test_project_closure_independence(self) -> None:
        spec_a = StringMatchSpec(value="alpha", case_insensitive=False, negated=False)
        spec_b = StringMatchSpec(value="beta", case_insensitive=False, negated=False)
        cond_a = UserConditions.by_project_name_contains(spec_a)
        cond_b = UserConditions.by_project_name_contains(spec_b)
        sql_a = str(cond_a().compile(compile_kwargs={"literal_binds": True}))
        sql_b = str(cond_b().compile(compile_kwargs={"literal_binds": True}))
        assert sql_a != sql_b
        assert "alpha" in sql_a
        assert "beta" in sql_b


class TestUserOrdersDomainNested:
    """Tests for Domain nested orders in UserOrders."""

    def test_by_domain_name_ascending(self) -> None:
        order = UserOrders.by_domain_name(ascending=True)
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_by_domain_name_descending(self) -> None:
        order = UserOrders.by_domain_name(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_by_domain_name_contains_scalar_subquery(self) -> None:
        order = UserOrders.by_domain_name(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "domains" in order_str
        assert "SELECT" in order_str.upper()

    def test_by_domain_created_at_ascending(self) -> None:
        order = UserOrders.by_domain_created_at(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "domains" in order_str
        assert "created_at" in order_str

    def test_by_domain_created_at_descending(self) -> None:
        order = UserOrders.by_domain_created_at(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_scalar_subquery_returns_clause_element(self) -> None:
        order = UserOrders.by_domain_name(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)


class TestUserOrdersProjectNested:
    """Tests for Project nested orders in UserOrders."""

    def test_by_project_name_ascending(self) -> None:
        order = UserOrders.by_project_name(ascending=True)
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_by_project_name_descending(self) -> None:
        order = UserOrders.by_project_name(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_by_project_name_contains_min_aggregation(self) -> None:
        order = UserOrders.by_project_name(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "min" in order_str.lower()
        assert "association_groups_users" in order_str
        assert "groups" in order_str

    def test_scalar_project_returns_clause_element(self) -> None:
        order = UserOrders.by_project_name(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)


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
        return UserDBSource(db=db_with_cleanup)

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
                session.add(
                    DomainRow(
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
                    )
                )
            await session.flush()

            # Projects
            for pid, pname, dom in [
                (project_alpha_id, "alpha-project", active_domain),
                (project_beta_id, "beta-project", inactive_domain),
            ]:
                session.add(
                    GroupRow(
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

            # M:N associations
            for uid, pid in [
                (user_active_uuid, project_alpha_id),
                (user_inactive_uuid, project_beta_id),
            ]:
                session.add(AssocGroupUserRow(user_id=uid, group_id=pid))

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

    @pytest.mark.asyncio
    async def test_search_users_with_domain_is_active_filter(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """search_users with by_domain_is_active(True) returns only users in active domains."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[UserConditions.by_domain_is_active(True)],
            orders=[],
        )
        result = await user_db_source.search_users(querier)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_active_domain

    @pytest.mark.asyncio
    async def test_search_users_with_domain_description_contains_filter(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """search_users with domain description filter returns matching users."""
        spec = StringMatchSpec(value="Research", case_insensitive=True, negated=False)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[UserConditions.by_domain_description_contains(spec)],
            orders=[],
        )
        result = await user_db_source.search_users(querier)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_active_domain

    # ---- Project nested filter tests ----

    @pytest.mark.asyncio
    async def test_search_users_with_project_name_contains_filter(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """search_users with by_project_name_contains filters by project membership."""
        spec = StringMatchSpec(value="alpha", case_insensitive=False, negated=False)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[UserConditions.by_project_name_contains(spec)],
            orders=[],
        )
        result = await user_db_source.search_users(querier)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_active_domain

    @pytest.mark.asyncio
    async def test_search_users_with_project_name_negated_filter(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """Negated project name filter excludes matching users."""
        spec = StringMatchSpec(value="alpha", case_insensitive=False, negated=True)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[UserConditions.by_project_name_contains(spec)],
            orders=[],
        )
        result = await user_db_source.search_users(querier)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_inactive_domain

    # ---- Domain nested order tests ----

    @pytest.mark.asyncio
    async def test_search_users_ordered_by_domain_name(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """search_users with by_domain_name order sorts users by correlated domain name."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[UserOrders.by_domain_name(ascending=True)],
        )
        result = await user_db_source.search_users(querier)

        assert result.total_count == 2
        # Sorted by domain name ascending: active-dom < inactive-dom
        assert result.items[0].uuid == search_fixture.user_in_active_domain
        assert result.items[1].uuid == search_fixture.user_in_inactive_domain

    # ---- Project nested order tests ----

    @pytest.mark.asyncio
    async def test_search_users_ordered_by_project_name(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """search_users with by_project_name order sorts by MIN(project name)."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[UserOrders.by_project_name(ascending=True)],
        )
        result = await user_db_source.search_users(querier)

        assert result.total_count == 2
        # alpha-project < beta-project
        assert result.items[0].uuid == search_fixture.user_in_active_domain
        assert result.items[1].uuid == search_fixture.user_in_inactive_domain

    # ---- Combined filter + order tests ----

    @pytest.mark.asyncio
    async def test_search_users_combined_domain_filter_and_project_order(
        self,
        user_db_source: UserDBSource,
        search_fixture: UserSearchFixture,
    ) -> None:
        """Combining domain filter + project order in single search call."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[UserConditions.by_domain_is_active(True)],
            orders=[UserOrders.by_project_name(ascending=True)],
        )
        result = await user_db_source.search_users(querier)

        assert result.total_count == 1
        assert result.items[0].uuid == search_fixture.user_in_active_domain
