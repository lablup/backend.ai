"""Tests for the project search declarations: linked correlations and column orders."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.filter_specs import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.user.types import UserStatus
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
from ai.backend.manager.models.project import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.project.deprecated_search import (
    DeprecatedProjectConditions,
    DeprecatedProjectOrders,
)
from ai.backend.manager.models.project.searchable_fields import ProjectSearchableFields
from ai.backend.manager.models.project.searchers import ProjectSearcher
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
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.project.db_source import ProjectDBSource
from ai.backend.testutils.db import TableOrORM, with_tables

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
]


class TestProjectLinkedDomainFilters:
    """The deprecated domain filter gathers the domain conditions into one EXISTS."""

    def test_exists_domain_returns_callable(self) -> None:
        condition = DeprecatedProjectConditions.exists_domain_combined([
            DomainSearchableFields.own.is_active.filter.equals(True)
        ])
        assert callable(condition)

    def test_by_domain_is_active_true(self) -> None:
        condition = DeprecatedProjectConditions.exists_domain_combined([
            DomainSearchableFields.own.is_active.filter.equals(True)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "is_active" in sql

    def test_by_domain_is_active_false(self) -> None:
        condition = DeprecatedProjectConditions.exists_domain_combined([
            DomainSearchableFields.own.is_active.filter.equals(False)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "is_active" in sql

    def test_exists_domain_combined_single_exists(self) -> None:
        """Combined helper wraps raw column conditions into single EXISTS."""

        def cond_is_active() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.is_active == True  # noqa: E712

        def cond_name_like() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.description.like("%test%")

        conditions: list[QueryCondition] = [cond_is_active, cond_name_like]
        combined = DeprecatedProjectConditions.exists_domain_combined(conditions)
        sql = str(combined().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert sql.count("EXISTS") == 1

    def test_exists_domain_combined_returns_column_element(self) -> None:
        conditions: list[QueryCondition] = []
        combined = DeprecatedProjectConditions.exists_domain_combined(conditions)
        result = combined()
        assert isinstance(result, sa.sql.expression.ColumnElement)


class TestProjectDomainNameOrder:
    """The domain name order reads the project's own column."""

    def test_by_domain_name_ascending(self) -> None:
        order = ProjectSearchableFields.own.domain_name.order.apply(ascending=True)
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_by_domain_name_descending(self) -> None:
        order = ProjectSearchableFields.own.domain_name.order.apply(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_by_domain_name_reads_the_projects_column(self) -> None:
        order = ProjectSearchableFields.own.domain_name.order.apply(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "groups.domain_name" in order_str

    def test_returns_clause_element(self) -> None:
        order = ProjectSearchableFields.own.domain_name.order.apply(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)


class TestGroupNestedSearchIntegration:
    """DB integration tests: nested filter/order applied via ProjectDBSource.search_projects."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, _WITH_TABLES):
            yield database_connection

    @pytest.fixture
    async def group_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ProjectDBSource:
        return ProjectDBSource(db=db_with_cleanup, v2_ops_provider=V2DBOpsProvider(db_with_cleanup))

    @pytest.fixture
    async def two_domains_with_projects(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> dict[str, list[uuid.UUID]]:
        """Create two domains (active/inactive) each with one project.

        Returns mapping of domain_name -> [project_id].
        """
        active_domain = f"active-dom-{uuid.uuid4().hex[:8]}"
        inactive_domain = f"inactive-dom-{uuid.uuid4().hex[:8]}"
        result: dict[str, list[uuid.UUID]] = {}

        async with db_with_cleanup.begin_session() as session:
            for domain_name, is_active, desc in [
                (active_domain, True, "Research lab"),
                (inactive_domain, False, "Archived department"),
            ]:
                domain_id = DomainID(uuid.uuid4())
                domain = DomainRow(
                    id=domain_id,
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

            policy = ProjectResourcePolicyRow(
                name=f"pol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(policy)
            await session.flush()

            for domain_name in [active_domain, inactive_domain]:
                gid = uuid.uuid4()
                group = ProjectRow(
                    id=gid,
                    name=f"proj-{gid.hex[:8]}",
                    description="test project",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=policy.name,
                    type=ProjectType.GENERAL,
                )
                session.add(group)
                result[domain_name] = [gid]

            await session.commit()

        return result

    async def test_search_projects_with_domain_is_active_filter(
        self,
        group_db_source: ProjectDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """search_projects with by_domain_is_active(True) returns only projects in active domains."""
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_domain_combined([
                    DomainSearchableFields.own.is_active.filter.equals(True)
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 1
        active_domain = [d for d, _ in two_domains_with_projects.items() if "active-dom" in d][0]
        assert result.items[0].id == two_domains_with_projects[active_domain][0]

    async def test_search_projects_with_domain_name_filter(
        self,
        group_db_source: ProjectDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """The deprecated domain filter narrows by the holding domain's name."""
        active_domain = [
            d
            for d in two_domains_with_projects
            if "active-dom" in d and not d.startswith("inactive")
        ][0]
        spec = StringMatchSpec(value=active_domain, case_insensitive=False, negated=False)
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_domain_combined([
                    DomainSearchableFields.own.name.filter.equals(spec)
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 1
        assert result.items[0].id == two_domains_with_projects[active_domain][0]

    async def test_search_projects_with_negated_domain_name_filter(
        self,
        group_db_source: ProjectDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """A negated domain name condition excludes that domain's projects."""
        active_domain = [
            d
            for d in two_domains_with_projects
            if "active-dom" in d and not d.startswith("inactive")
        ][0]
        spec = StringMatchSpec(value=active_domain, case_insensitive=False, negated=True)
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_domain_combined([
                    DomainSearchableFields.own.name.filter.equals(spec)
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 1
        assert result.items[0].id != two_domains_with_projects[active_domain][0]

    async def test_search_projects_ordered_by_domain_name(
        self,
        group_db_source: ProjectDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """search_projects with by_domain_name order sorts by correlated domain name."""
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[ProjectSearchableFields.own.domain_name.order.apply(ascending=True)],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 2
        domain_names = sorted(two_domains_with_projects.keys())
        assert result.items[0].id == two_domains_with_projects[domain_names[0]][0]
        assert result.items[1].id == two_domains_with_projects[domain_names[1]][0]

    async def test_search_projects_combined_domain_filter_and_order(
        self,
        group_db_source: ProjectDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """Combining nested filter + nested order in single search call."""
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_domain_combined([
                    DomainSearchableFields.own.is_active.filter.equals(True)
                ])
            ],
            orders=[ProjectSearchableFields.own.domain_name.order.apply(ascending=True)],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 1


class TestGroupConditionsUserIdFilters:
    """The deprecated user filter narrows by the enrolled user's id."""

    def test_by_user_id_equals_generates_exists(self) -> None:
        user_uuid = uuid.uuid4()
        spec = UUIDEqualMatchSpec(value=user_uuid, negated=False)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.uuid.filter.equals(spec)
        ])
        sql = str(condition().compile())
        assert "EXISTS" in sql
        assert "users" in sql
        assert "association_groups_users" in sql

    def test_by_user_id_equals_negated(self) -> None:
        user_uuid = uuid.uuid4()
        spec = UUIDEqualMatchSpec(value=user_uuid, negated=True)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.uuid.filter.equals(spec)
        ])
        sql = str(condition().compile())
        assert "EXISTS" in sql
        assert "!=" in sql or "NOT" in sql.upper()

    def test_by_user_id_in_generates_exists(self) -> None:
        user_uuids = [uuid.uuid4(), uuid.uuid4()]
        spec = UUIDInMatchSpec(values=user_uuids, negated=False)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.uuid.filter.in_(spec)
        ])
        sql = str(condition().compile())
        assert "EXISTS" in sql
        assert "users" in sql
        assert "association_groups_users" in sql
        assert "IN" in sql.upper()

    def test_by_user_id_in_negated(self) -> None:
        user_uuids = [uuid.uuid4(), uuid.uuid4()]
        spec = UUIDInMatchSpec(values=user_uuids, negated=True)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.uuid.filter.in_(spec)
        ])
        sql = str(condition().compile())
        assert "EXISTS" in sql
        assert "NOT IN" in sql.upper()


class TestGroupConditionsUserNestedFilters:
    """The deprecated user filter narrows by the enrolled user's own columns."""

    def test_by_user_username_contains_generates_exists(self) -> None:
        spec = StringMatchSpec(value="alice", case_insensitive=False, negated=False)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.username.filter.contains(spec)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql
        assert "association_groups_users" in sql

    def test_by_user_username_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="alice", case_insensitive=True, negated=False)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.username.filter.contains(spec)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "lower" in sql

    def test_by_user_username_contains_negated(self) -> None:
        spec = StringMatchSpec(value="alice", case_insensitive=False, negated=True)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.username.filter.contains(spec)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "NOT LIKE" in sql.upper()

    def test_by_user_username_equals_generates_exists(self) -> None:
        spec = StringMatchSpec(value="alice", case_insensitive=False, negated=False)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.username.filter.equals(spec)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql

    def test_by_user_username_equals_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="Alice", case_insensitive=True, negated=False)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.username.filter.equals(spec)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "lower" in sql

    def test_by_user_email_contains_generates_exists(self) -> None:
        spec = StringMatchSpec(value="@example", case_insensitive=False, negated=False)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.email.filter.contains(spec)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql

    def test_by_user_email_equals_generates_exists(self) -> None:
        spec = StringMatchSpec(value="alice@example.com", case_insensitive=False, negated=False)
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.email.filter.equals(spec)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "users" in sql

    def test_by_user_is_active_true(self) -> None:
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.status.filter.equals(UserStatus.ACTIVE)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "status" in sql

    def test_by_user_is_active_false(self) -> None:
        condition = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.status.filter.not_equals(UserStatus.ACTIVE)
        ])
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "status" in sql

    def test_exists_user_combined_single_exists(self) -> None:
        """Combined helper wraps raw column conditions into single EXISTS."""

        def cond_status() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.status == UserStatus.ACTIVE

        def cond_username_like() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.username.like("%test%")

        conditions: list[QueryCondition] = [cond_status, cond_username_like]
        combined = DeprecatedProjectConditions.exists_user_combined(conditions)
        sql = str(combined().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert sql.count("EXISTS") == 1
        assert "association_groups_users" in sql

    def test_exists_user_combined_returns_column_element(self) -> None:
        conditions: list[QueryCondition] = []
        combined = DeprecatedProjectConditions.exists_user_combined(conditions)
        result = combined()
        assert isinstance(result, sa.sql.expression.ColumnElement)

    def test_closure_independence(self) -> None:
        spec_a = StringMatchSpec(value="alice", case_insensitive=False, negated=False)
        spec_b = StringMatchSpec(value="bob", case_insensitive=False, negated=False)
        cond_a = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.username.filter.contains(spec_a)
        ])
        cond_b = DeprecatedProjectConditions.exists_user_combined([
            UserSearchableFields.own.username.filter.contains(spec_b)
        ])
        sql_a = str(cond_a().compile(compile_kwargs={"literal_binds": True}))
        sql_b = str(cond_b().compile(compile_kwargs={"literal_binds": True}))
        assert sql_a != sql_b
        assert "alice" in sql_a
        assert "bob" in sql_b


class TestGroupOrdersUserNested:
    """The deprecated orders fold the project's users with MIN."""

    def test_by_user_username_ascending(self) -> None:
        order = DeprecatedProjectOrders.by_user_username(ascending=True)
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_by_user_username_descending(self) -> None:
        order = DeprecatedProjectOrders.by_user_username(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_by_user_username_contains_min_subquery(self) -> None:
        order = DeprecatedProjectOrders.by_user_username(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "users" in order_str
        assert "min" in order_str.lower()
        assert "association_groups_users" in order_str

    def test_by_user_email_ascending(self) -> None:
        order = DeprecatedProjectOrders.by_user_email(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "users" in order_str
        assert "min" in order_str.lower()

    def test_by_user_email_descending(self) -> None:
        order = DeprecatedProjectOrders.by_user_email(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_returns_clause_element(self) -> None:
        order = DeprecatedProjectOrders.by_user_username(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)


class TestGroupUserNestedSearchIntegration:
    """DB integration tests: User nested filter/order via ProjectDBSource.search_projects."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, _WITH_TABLES):
            yield database_connection

    @pytest.fixture
    async def group_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ProjectDBSource:
        return ProjectDBSource(db=db_with_cleanup, v2_ops_provider=V2DBOpsProvider(db_with_cleanup))

    @pytest.fixture
    async def projects_with_users(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> dict[str, dict[str, Any]]:
        """Create a domain with two projects, each associated with one user.

        Returns mapping with project info including user details.
        """
        domain_name = f"test-dom-{uuid.uuid4().hex[:8]}"
        result: dict[str, dict[str, Any]] = {}

        async with db_with_cleanup.begin_session() as session:
            domain_id = DomainID(uuid.uuid4())
            domain = DomainRow(
                id=domain_id,
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
            await session.flush()

            user_policy = UserResourcePolicyRow(
                name=f"upol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
            session.add(user_policy)

            project_policy = ProjectResourcePolicyRow(
                name=f"ppol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(project_policy)
            await session.flush()

            active_user_id = uuid.uuid4()
            active_user = UserRow(
                uuid=active_user_id,
                username="alice-active",
                email="alice@example.com",
                password=PasswordInfo(
                    password="test_password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=100_000,
                    salt_size=32,
                ),
                domain_id=domain_id,
                need_password_change=False,
                full_name="Alice Active",
                description="Active user",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=user_policy.name,
            )
            session.add(active_user)

            inactive_user_id = uuid.uuid4()
            inactive_user = UserRow(
                uuid=inactive_user_id,
                username="bob-inactive",
                email="bob@example.com",
                password=PasswordInfo(
                    password="test_password",
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=100_000,
                    salt_size=32,
                ),
                domain_id=domain_id,
                need_password_change=False,
                full_name="Bob Inactive",
                description="Inactive user",
                status=UserStatus.INACTIVE,
                status_info="admin-requested",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=user_policy.name,
            )
            session.add(inactive_user)
            await session.flush()

            proj_a_id = uuid.uuid4()
            proj_a = ProjectRow(
                id=proj_a_id,
                name="proj-alpha",
                description="Alpha project",
                is_active=True,
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                integration_id=None,
                resource_policy=project_policy.name,
                type=ProjectType.GENERAL,
            )
            session.add(proj_a)

            proj_b_id = uuid.uuid4()
            proj_b = ProjectRow(
                id=proj_b_id,
                name="proj-beta",
                description="Beta project",
                is_active=True,
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                integration_id=None,
                resource_policy=project_policy.name,
                type=ProjectType.GENERAL,
            )
            session.add(proj_b)
            await session.flush()

            assoc_a = AssocGroupUserRow(
                group_id=proj_a_id,
                user_id=active_user_id,
            )
            session.add(assoc_a)

            assoc_b = AssocGroupUserRow(
                group_id=proj_b_id,
                user_id=inactive_user_id,
            )
            session.add(assoc_b)

            await session.commit()

        result["proj_alpha"] = {
            "project_id": proj_a_id,
            "user_id": active_user_id,
            "username": "alice-active",
            "email": "alice@example.com",
            "is_active": True,
        }
        result["proj_beta"] = {
            "project_id": proj_b_id,
            "user_id": inactive_user_id,
            "username": "bob-inactive",
            "email": "bob@example.com",
            "is_active": False,
        }
        return result

    async def test_search_with_user_id_equals_filter(
        self,
        group_db_source: ProjectDBSource,
        projects_with_users: dict[str, dict[str, Any]],
    ) -> None:
        """Filter projects by user UUID (equals)."""
        alpha_info = projects_with_users["proj_alpha"]
        spec = UUIDEqualMatchSpec(value=alpha_info["user_id"], negated=False)
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_user_combined([
                    UserSearchableFields.own.uuid.filter.equals(spec)
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 1
        assert result.items[0].id == alpha_info["project_id"]

    async def test_search_with_user_id_in_filter(
        self,
        group_db_source: ProjectDBSource,
        projects_with_users: dict[str, dict[str, Any]],
    ) -> None:
        """Filter projects by user UUID (in list)."""
        alpha_info = projects_with_users["proj_alpha"]
        beta_info = projects_with_users["proj_beta"]
        spec = UUIDInMatchSpec(values=[alpha_info["user_id"], beta_info["user_id"]], negated=False)
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_user_combined([
                    UserSearchableFields.own.uuid.filter.in_(spec)
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 2

    async def test_search_with_user_username_filter(
        self,
        group_db_source: ProjectDBSource,
        projects_with_users: dict[str, dict[str, Any]],
    ) -> None:
        """Filter projects by user username (contains)."""
        spec = StringMatchSpec(value="alice", case_insensitive=True, negated=False)
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_user_combined([
                    UserSearchableFields.own.username.filter.contains(spec)
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 1
        assert result.items[0].id == projects_with_users["proj_alpha"]["project_id"]

    async def test_search_with_user_email_filter(
        self,
        group_db_source: ProjectDBSource,
        projects_with_users: dict[str, dict[str, Any]],
    ) -> None:
        """Filter projects by user email (contains)."""
        spec = StringMatchSpec(value="bob@", case_insensitive=False, negated=False)
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_user_combined([
                    UserSearchableFields.own.email.filter.contains(spec)
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 1
        assert result.items[0].id == projects_with_users["proj_beta"]["project_id"]

    async def test_search_with_user_is_active_filter(
        self,
        group_db_source: ProjectDBSource,
        projects_with_users: dict[str, dict[str, Any]],
    ) -> None:
        """Filter projects by user active status."""
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_user_combined([
                    UserSearchableFields.own.status.filter.equals(UserStatus.ACTIVE)
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 1
        assert result.items[0].id == projects_with_users["proj_alpha"]["project_id"]

    async def test_search_ordered_by_user_username(
        self,
        group_db_source: ProjectDBSource,
        projects_with_users: dict[str, dict[str, Any]],
    ) -> None:
        """Order projects by user username (MIN aggregation)."""
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[DeprecatedProjectOrders.by_user_username(ascending=True)],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 2
        # alice < bob alphabetically
        assert result.items[0].id == projects_with_users["proj_alpha"]["project_id"]
        assert result.items[1].id == projects_with_users["proj_beta"]["project_id"]

    async def test_search_ordered_by_user_email(
        self,
        group_db_source: ProjectDBSource,
        projects_with_users: dict[str, dict[str, Any]],
    ) -> None:
        """Order projects by user email (MIN aggregation)."""
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[DeprecatedProjectOrders.by_user_email(ascending=True)],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 2
        # alice@example.com < bob@example.com
        assert result.items[0].id == projects_with_users["proj_alpha"]["project_id"]
        assert result.items[1].id == projects_with_users["proj_beta"]["project_id"]


class TestGroupUserNestedSameMember:
    """One EXISTS over every user condition, so one member has to satisfy them all."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, _WITH_TABLES):
            yield database_connection

    @pytest.fixture
    async def group_db_source(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> ProjectDBSource:
        return ProjectDBSource(db=db_with_cleanup, v2_ops_provider=V2DBOpsProvider(db_with_cleanup))

    @pytest.fixture
    async def project_with_two_members(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> uuid.UUID:
        """One project holding carol and dave, whose usernames and emails do not cross."""
        domain_name = f"two-member-dom-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as session:
            domain_id = DomainID(uuid.uuid4())
            session.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="Two member domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    allowed_docker_registries=[],
                    dotfiles=b"",
                    integration_id=None,
                )
            )
            await session.flush()

            user_policy = UserResourcePolicyRow(
                name=f"upol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
            project_policy = ProjectResourcePolicyRow(
                name=f"ppol-{uuid.uuid4().hex[:8]}",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(user_policy)
            session.add(project_policy)
            await session.flush()

            member_ids: list[uuid.UUID] = []
            for username, email in [("carol", "carol@example.com"), ("dave", "dave@example.com")]:
                member_id = uuid.uuid4()
                session.add(
                    UserRow(
                        uuid=member_id,
                        username=username,
                        email=email,
                        password=PasswordInfo(
                            password="test_password",
                            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                            rounds=100_000,
                            salt_size=32,
                        ),
                        domain_id=domain_id,
                        need_password_change=False,
                        full_name=username,
                        description="member",
                        status=UserStatus.ACTIVE,
                        status_info="admin-requested",
                        domain_name=domain_name,
                        role=UserRole.USER,
                        resource_policy=user_policy.name,
                    )
                )
                member_ids.append(member_id)
            await session.flush()

            session.add(
                ProjectRow(
                    id=project_id,
                    name=f"proj-{project_id.hex[:8]}",
                    description="two member project",
                    is_active=True,
                    domain_name=domain_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts=VFolderHostPermissionMap(),
                    integration_id=None,
                    resource_policy=project_policy.name,
                    type=ProjectType.GENERAL,
                )
            )
            await session.flush()

            for member_id in member_ids:
                session.add(AssocGroupUserRow(group_id=project_id, user_id=member_id))

            await session.commit()

        return project_id

    async def test_conditions_met_by_one_member_match(
        self,
        group_db_source: ProjectDBSource,
        project_with_two_members: uuid.UUID,
    ) -> None:
        """Carol's username and Carol's email are the same member, so the project matches."""
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_user_combined([
                    UserSearchableFields.own.username.filter.contains(
                        StringMatchSpec(value="carol", case_insensitive=False, negated=False)
                    ),
                    UserSearchableFields.own.email.filter.contains(
                        StringMatchSpec(value="carol@", case_insensitive=False, negated=False)
                    ),
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 1
        assert result.items[0].id == project_with_two_members

    async def test_conditions_split_across_members_do_not_match(
        self,
        group_db_source: ProjectDBSource,
        project_with_two_members: uuid.UUID,
    ) -> None:
        """Carol's username and Dave's email are different members, so nothing matches."""
        searcher = ProjectSearcher(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[
                DeprecatedProjectConditions.exists_user_combined([
                    UserSearchableFields.own.username.filter.contains(
                        StringMatchSpec(value="carol", case_insensitive=False, negated=False)
                    ),
                    UserSearchableFields.own.email.filter.contains(
                        StringMatchSpec(value="dave@", case_insensitive=False, negated=False)
                    ),
                ])
            ],
            orders=[],
        )
        result = await group_db_source.search_projects(searcher)

        assert result.total_count == 0
