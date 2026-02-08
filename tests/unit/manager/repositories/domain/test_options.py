"""Tests for DomainConditions and DomainOrders nested filter/order helpers."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
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
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination, QueryCondition
from ai.backend.manager.repositories.domain.db_source import DomainDBSource
from ai.backend.manager.repositories.domain.options import (
    DomainConditions,
    DomainOrders,
)
from ai.backend.testutils.db import with_tables


def _make_password_info() -> PasswordInfo:
    return PasswordInfo(
        password="test_password",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


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


class TestDomainConditionsDescriptionFilters:
    """Tests for description filter conditions in DomainConditions."""

    def test_by_description_contains_returns_callable(self) -> None:
        spec = StringMatchSpec(value="test", case_insensitive=False, negated=False)
        condition = DomainConditions.by_description_contains(spec)
        assert callable(condition)

    def test_by_description_contains_generates_like(self) -> None:
        spec = StringMatchSpec(value="research", case_insensitive=False, negated=False)
        condition = DomainConditions.by_description_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "LIKE" in sql.upper()
        assert "%research%" in sql

    def test_by_description_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="research", case_insensitive=True, negated=False)
        condition = DomainConditions.by_description_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "lower" in sql

    def test_by_description_contains_negated(self) -> None:
        spec = StringMatchSpec(value="research", case_insensitive=False, negated=True)
        condition = DomainConditions.by_description_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "NOT LIKE" in sql.upper()

    def test_by_description_equals_generates_equals(self) -> None:
        spec = StringMatchSpec(value="exact", case_insensitive=False, negated=False)
        condition = DomainConditions.by_description_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "exact" in sql

    def test_by_description_equals_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="Exact", case_insensitive=True, negated=False)
        condition = DomainConditions.by_description_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "lower" in sql

    def test_by_description_equals_negated(self) -> None:
        spec = StringMatchSpec(value="exact", case_insensitive=False, negated=True)
        condition = DomainConditions.by_description_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        # sa.not_(col == val) compiles as col != val
        assert "!=" in sql or "NOT" in sql.upper()

    def test_by_description_starts_with(self) -> None:
        spec = StringMatchSpec(value="Research", case_insensitive=False, negated=False)
        condition = DomainConditions.by_description_starts_with(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "LIKE" in sql.upper()
        assert "Research%" in sql

    def test_by_description_ends_with(self) -> None:
        spec = StringMatchSpec(value="lab", case_insensitive=False, negated=False)
        condition = DomainConditions.by_description_ends_with(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "LIKE" in sql.upper()
        assert "%lab" in sql


class TestDomainConditionsProjectNestedFilters:
    """Tests for Project nested filter conditions in DomainConditions."""

    def test_by_project_name_contains_generates_exists(self) -> None:
        spec = StringMatchSpec(value="ml", case_insensitive=False, negated=False)
        condition = DomainConditions.by_project_name_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "groups" in sql

    def test_by_project_name_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="ml", case_insensitive=True, negated=False)
        condition = DomainConditions.by_project_name_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "lower" in sql

    def test_by_project_name_contains_negated(self) -> None:
        spec = StringMatchSpec(value="ml", case_insensitive=False, negated=True)
        condition = DomainConditions.by_project_name_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "NOT LIKE" in sql.upper()

    def test_by_project_name_equals_generates_exists(self) -> None:
        spec = StringMatchSpec(value="project-ml", case_insensitive=False, negated=False)
        condition = DomainConditions.by_project_name_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "groups" in sql

    def test_by_project_is_active_true(self) -> None:
        condition = DomainConditions.by_project_is_active(True)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "is_active" in sql

    def test_by_project_is_active_false(self) -> None:
        condition = DomainConditions.by_project_is_active(False)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "is_active" in sql

    def test_exists_project_combined_single_exists(self) -> None:
        """Combined helper wraps raw column conditions into single EXISTS."""

        def cond_is_active() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.is_active == True  # noqa: E712

        def cond_name_like() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.name.like("%test%")

        conditions: list[QueryCondition] = [cond_is_active, cond_name_like]
        combined = DomainConditions.exists_project_combined(conditions)
        sql = str(combined().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert sql.count("EXISTS") == 1

    def test_exists_project_combined_returns_column_element(self) -> None:
        conditions: list[QueryCondition] = []
        combined = DomainConditions.exists_project_combined(conditions)
        result = combined()
        assert isinstance(result, sa.sql.expression.ColumnElement)

    def test_closure_independence(self) -> None:
        spec_a = StringMatchSpec(value="alpha", case_insensitive=False, negated=False)
        spec_b = StringMatchSpec(value="beta", case_insensitive=False, negated=False)
        cond_a = DomainConditions.by_project_name_contains(spec_a)
        cond_b = DomainConditions.by_project_name_contains(spec_b)
        sql_a = str(cond_a().compile(compile_kwargs={"literal_binds": True}))
        sql_b = str(cond_b().compile(compile_kwargs={"literal_binds": True}))
        assert sql_a != sql_b
        assert "alpha" in sql_a
        assert "beta" in sql_b


class TestDomainConditionsUserNestedFilters:
    """Tests for User nested filter conditions in DomainConditions."""

    def test_by_user_username_contains_generates_exists(self) -> None:
        spec = StringMatchSpec(value="alice", case_insensitive=False, negated=False)
        condition = DomainConditions.by_user_username_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql

    def test_by_user_username_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="alice", case_insensitive=True, negated=False)
        condition = DomainConditions.by_user_username_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "lower" in sql

    def test_by_user_username_equals_generates_exists(self) -> None:
        spec = StringMatchSpec(value="alice", case_insensitive=False, negated=False)
        condition = DomainConditions.by_user_username_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql

    def test_by_user_email_contains_generates_exists(self) -> None:
        spec = StringMatchSpec(value="@example.com", case_insensitive=False, negated=False)
        condition = DomainConditions.by_user_email_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql

    def test_by_user_email_equals_generates_exists(self) -> None:
        spec = StringMatchSpec(value="alice@example.com", case_insensitive=False, negated=False)
        condition = DomainConditions.by_user_email_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql

    def test_exists_user_combined_single_exists(self) -> None:
        """Combined helper wraps raw column conditions into single EXISTS."""

        def cond_username_like() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.username.like("%alice%")

        def cond_email_like() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.email.like("%@example.com%")

        conditions: list[QueryCondition] = [cond_username_like, cond_email_like]
        combined = DomainConditions.exists_user_combined(conditions)
        sql = str(combined().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert sql.count("EXISTS") == 1

    def test_exists_user_combined_returns_column_element(self) -> None:
        conditions: list[QueryCondition] = []
        combined = DomainConditions.exists_user_combined(conditions)
        result = combined()
        assert isinstance(result, sa.sql.expression.ColumnElement)

    def test_by_user_is_active_true(self) -> None:
        condition = DomainConditions.by_user_is_active(True)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql
        assert "status" in sql

    def test_by_user_is_active_false(self) -> None:
        condition = DomainConditions.by_user_is_active(False)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql
        assert "status" in sql

    def test_closure_independence(self) -> None:
        spec_a = StringMatchSpec(value="alice", case_insensitive=False, negated=False)
        spec_b = StringMatchSpec(value="bob", case_insensitive=False, negated=False)
        cond_a = DomainConditions.by_user_username_contains(spec_a)
        cond_b = DomainConditions.by_user_username_contains(spec_b)
        sql_a = str(cond_a().compile(compile_kwargs={"literal_binds": True}))
        sql_b = str(cond_b().compile(compile_kwargs={"literal_binds": True}))
        assert sql_a != sql_b
        assert "alice" in sql_a
        assert "bob" in sql_b


class TestDomainOrdersProjectNested:
    """Tests for Project nested orders in DomainOrders."""

    def test_by_project_name_ascending(self) -> None:
        order = DomainOrders.by_project_name(ascending=True)
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_by_project_name_descending(self) -> None:
        order = DomainOrders.by_project_name(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_by_project_name_contains_min_and_groups(self) -> None:
        order = DomainOrders.by_project_name(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "groups" in order_str
        assert "min" in order_str.lower()

    def test_scalar_subquery_returns_clause_element(self) -> None:
        order = DomainOrders.by_project_name(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)


class TestDomainOrdersUserNested:
    """Tests for User nested orders in DomainOrders."""

    def test_by_user_username_ascending(self) -> None:
        order = DomainOrders.by_user_username(ascending=True)
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_by_user_username_descending(self) -> None:
        order = DomainOrders.by_user_username(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_by_user_username_contains_min_and_users(self) -> None:
        order = DomainOrders.by_user_username(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "users" in order_str
        assert "min" in order_str.lower()

    def test_scalar_subquery_returns_clause_element(self) -> None:
        order = DomainOrders.by_user_username(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)

    def test_by_user_email_ascending(self) -> None:
        order = DomainOrders.by_user_email(ascending=True)
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_by_user_email_descending(self) -> None:
        order = DomainOrders.by_user_email(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_by_user_email_contains_min_and_users(self) -> None:
        order = DomainOrders.by_user_email(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "users" in order_str
        assert "min" in order_str.lower()

    def test_by_user_email_returns_clause_element(self) -> None:
        order = DomainOrders.by_user_email(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)


class TestDomainNestedSearchIntegration:
    """DB integration tests: nested filter/order applied via DomainDBSource.search_domains."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, _WITH_TABLES):
            yield database_connection

    @pytest.fixture
    async def domain_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainDBSource:
        return DomainDBSource(db=db_with_cleanup)

    @pytest.fixture
    async def two_domains_with_children(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> dict[str, dict[str, str]]:
        """Create two domains each with one project and one user.

        Returns mapping of domain_name -> {project_name, username, email}.
        """
        domain_alpha = f"domain-alpha-{uuid.uuid4().hex[:8]}"
        domain_beta = f"domain-beta-{uuid.uuid4().hex[:8]}"
        result: dict[str, dict[str, str]] = {}

        async with db_with_cleanup.begin_session() as session:
            for domain_name, is_active, desc in [
                (domain_alpha, True, "Research lab"),
                (domain_beta, False, "Archived department"),
            ]:
                domain = DomainRow(
                    name=domain_name,
                    description=desc,
                    is_active=is_active,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                    dotfiles=b"",
                    integration_id=None,
                )
                session.add(domain)

            await session.flush()

            # Create resource policies
            proj_policy = ProjectResourcePolicyRow(
                name=f"pol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(proj_policy)

            user_policy = UserResourcePolicyRow(
                name=f"upol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
            session.add(user_policy)

            kp_policy = KeyPairResourcePolicyRow(
                name=f"kppol-{uuid.uuid4().hex[:8]}",
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=1,
                max_containers_per_session=1,
                idle_timeout=3600,
            )
            session.add(kp_policy)
            await session.flush()

            keypair_data: list[tuple[str, uuid.UUID]] = []
            for domain_name, proj_name, proj_active, uname, email in [
                (
                    domain_alpha,
                    "project-ml",
                    True,
                    "alice",
                    f"alice-{uuid.uuid4().hex[:8]}@example.com",
                ),
                (
                    domain_beta,
                    "project-archive",
                    False,
                    "bob",
                    f"bob-{uuid.uuid4().hex[:8]}@test.org",
                ),
            ]:
                gid = uuid.uuid4()
                group = GroupRow(
                    id=gid,
                    name=proj_name,
                    description="test project",
                    is_active=proj_active,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=proj_policy.name,
                    type=ProjectType.GENERAL,
                )
                session.add(group)

                user_uuid = uuid.uuid4()
                user = UserRow(
                    uuid=user_uuid,
                    username=uname,
                    email=email,
                    password=_make_password_info(),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="admin-requested",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy.name,
                )
                session.add(user)
                keypair_data.append((email, user_uuid))

                result[domain_name] = {
                    "project_name": proj_name,
                    "username": uname,
                    "email": email,
                }

            # Flush users first so FK on keypairs is satisfied
            await session.flush()

            for email, user_uuid in keypair_data:
                keypair = KeyPairRow(
                    user_id=email,
                    access_key=uuid.uuid4().hex[:20],
                    secret_key=uuid.uuid4().hex[:20],
                    user=user_uuid,
                    resource_policy=kp_policy.name,
                )
                session.add(keypair)

            await session.commit()

        return result

    @pytest.mark.asyncio
    async def test_search_with_description_filter(
        self,
        domain_db_source: DomainDBSource,
        two_domains_with_children: dict[str, dict[str, str]],
    ) -> None:
        """search_domains with description contains filter."""
        spec = StringMatchSpec(value="Research", case_insensitive=True, negated=False)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[DomainConditions.by_description_contains(spec)],
            orders=[],
        )
        result = await domain_db_source.search_domains(querier)

        assert result.total_count == 1
        alpha_domain = [d for d in two_domains_with_children if "alpha" in d][0]
        assert result.items[0].name == alpha_domain

    @pytest.mark.asyncio
    async def test_search_with_project_name_filter(
        self,
        domain_db_source: DomainDBSource,
        two_domains_with_children: dict[str, dict[str, str]],
    ) -> None:
        """search_domains with project name contains filter returns matching domain."""
        spec = StringMatchSpec(value="ml", case_insensitive=False, negated=False)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[DomainConditions.by_project_name_contains(spec)],
            orders=[],
        )
        result = await domain_db_source.search_domains(querier)

        assert result.total_count == 1
        alpha_domain = [d for d in two_domains_with_children if "alpha" in d][0]
        assert result.items[0].name == alpha_domain

    @pytest.mark.asyncio
    async def test_search_with_project_is_active_filter(
        self,
        domain_db_source: DomainDBSource,
        two_domains_with_children: dict[str, dict[str, str]],
    ) -> None:
        """search_domains with project is_active(True) returns domain with active project."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[DomainConditions.by_project_is_active(True)],
            orders=[],
        )
        result = await domain_db_source.search_domains(querier)

        assert result.total_count == 1
        alpha_domain = [d for d in two_domains_with_children if "alpha" in d][0]
        assert result.items[0].name == alpha_domain

    @pytest.mark.asyncio
    async def test_search_with_user_username_filter(
        self,
        domain_db_source: DomainDBSource,
        two_domains_with_children: dict[str, dict[str, str]],
    ) -> None:
        """search_domains with user username contains filter."""
        spec = StringMatchSpec(value="alice", case_insensitive=False, negated=False)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[DomainConditions.by_user_username_contains(spec)],
            orders=[],
        )
        result = await domain_db_source.search_domains(querier)

        assert result.total_count == 1
        alpha_domain = [d for d in two_domains_with_children if "alpha" in d][0]
        assert result.items[0].name == alpha_domain

    @pytest.mark.asyncio
    async def test_search_with_user_email_filter(
        self,
        domain_db_source: DomainDBSource,
        two_domains_with_children: dict[str, dict[str, str]],
    ) -> None:
        """search_domains with user email contains filter."""
        spec = StringMatchSpec(value="@test.org", case_insensitive=False, negated=False)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[DomainConditions.by_user_email_contains(spec)],
            orders=[],
        )
        result = await domain_db_source.search_domains(querier)

        assert result.total_count == 1
        beta_domain = [d for d in two_domains_with_children if "beta" in d][0]
        assert result.items[0].name == beta_domain

    @pytest.mark.asyncio
    async def test_search_ordered_by_project_name(
        self,
        domain_db_source: DomainDBSource,
        two_domains_with_children: dict[str, dict[str, str]],
    ) -> None:
        """search_domains ordered by project_name sorts by correlated MIN(project name)."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[DomainOrders.by_project_name(ascending=True)],
        )
        result = await domain_db_source.search_domains(querier)

        assert result.total_count == 2
        # project-archive < project-ml alphabetically
        beta_domain = [d for d in two_domains_with_children if "beta" in d][0]
        alpha_domain = [d for d in two_domains_with_children if "alpha" in d][0]
        assert result.items[0].name == beta_domain
        assert result.items[1].name == alpha_domain

    @pytest.mark.asyncio
    async def test_search_ordered_by_user_email(
        self,
        domain_db_source: DomainDBSource,
        two_domains_with_children: dict[str, dict[str, str]],
    ) -> None:
        """search_domains ordered by user email sorts by correlated MIN(email)."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[DomainOrders.by_user_email(ascending=True)],
        )
        result = await domain_db_source.search_domains(querier)

        assert result.total_count == 2
        # alice-*@example.com < bob-*@test.org alphabetically
        alpha_domain = [d for d in two_domains_with_children if "alpha" in d][0]
        assert result.items[0].name == alpha_domain

    @pytest.mark.asyncio
    async def test_search_with_user_is_active_filter(
        self,
        domain_db_source: DomainDBSource,
        two_domains_with_children: dict[str, dict[str, str]],
    ) -> None:
        """search_domains with user is_active(True) returns domain with active user."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[DomainConditions.by_user_is_active(True)],
            orders=[],
        )
        result = await domain_db_source.search_domains(querier)

        # Both users have status=ACTIVE, so both domains match
        assert result.total_count == 2

    @pytest.mark.asyncio
    async def test_search_combined_filter_and_order(
        self,
        domain_db_source: DomainDBSource,
        two_domains_with_children: dict[str, dict[str, str]],
    ) -> None:
        """Combining nested filter + nested order in single search call."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[DomainConditions.by_project_is_active(True)],
            orders=[DomainOrders.by_user_username(ascending=True)],
        )
        result = await domain_db_source.search_domains(querier)

        assert result.total_count == 1
        alpha_domain = [d for d in two_domains_with_children if "alpha" in d][0]
        assert result.items[0].name == alpha_domain
