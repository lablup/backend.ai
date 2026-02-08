"""Tests for GroupConditions and GroupOrders nested filter/order helpers."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap
from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
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
from ai.backend.manager.repositories.group.db_source import GroupDBSource
from ai.backend.manager.repositories.group.options import (
    GroupConditions,
    GroupOrders,
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


class TestGroupConditionsDomainNestedFilters:
    """Tests for Domain nested filter conditions in GroupConditions."""

    def test_exists_domain_returns_callable(self) -> None:
        spec = StringMatchSpec(value="test", case_insensitive=False, negated=False)
        condition = GroupConditions.by_domain_description_contains(spec)
        assert callable(condition)

    def test_by_domain_description_contains_generates_exists(self) -> None:
        spec = StringMatchSpec(value="research", case_insensitive=False, negated=False)
        condition = GroupConditions.by_domain_description_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "domains" in sql

    def test_by_domain_description_contains_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="research", case_insensitive=True, negated=False)
        condition = GroupConditions.by_domain_description_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        # Default dialect compiles ilike as lower(...) LIKE lower(...)
        assert "lower" in sql

    def test_by_domain_description_contains_negated(self) -> None:
        spec = StringMatchSpec(value="research", case_insensitive=False, negated=True)
        condition = GroupConditions.by_domain_description_contains(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "NOT LIKE" in sql.upper()

    def test_by_domain_description_equals_generates_exists(self) -> None:
        spec = StringMatchSpec(value="exact", case_insensitive=False, negated=False)
        condition = GroupConditions.by_domain_description_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "domains" in sql

    def test_by_domain_description_equals_case_insensitive(self) -> None:
        spec = StringMatchSpec(value="Exact", case_insensitive=True, negated=False)
        condition = GroupConditions.by_domain_description_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "lower" in sql

    def test_by_domain_description_equals_negated(self) -> None:
        spec = StringMatchSpec(value="exact", case_insensitive=False, negated=True)
        condition = GroupConditions.by_domain_description_equals(spec)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        # sa.not_(col == val) compiles as col != val
        assert "!=" in sql or "NOT" in sql.upper()

    def test_by_domain_is_active_true(self) -> None:
        condition = GroupConditions.by_domain_is_active(True)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "is_active" in sql

    def test_by_domain_is_active_false(self) -> None:
        condition = GroupConditions.by_domain_is_active(False)
        sql = str(condition().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert "is_active" in sql

    def test_closure_independence(self) -> None:
        spec_a = StringMatchSpec(value="alpha", case_insensitive=False, negated=False)
        spec_b = StringMatchSpec(value="beta", case_insensitive=False, negated=False)
        cond_a = GroupConditions.by_domain_description_contains(spec_a)
        cond_b = GroupConditions.by_domain_description_contains(spec_b)
        sql_a = str(cond_a().compile(compile_kwargs={"literal_binds": True}))
        sql_b = str(cond_b().compile(compile_kwargs={"literal_binds": True}))
        assert sql_a != sql_b
        assert "alpha" in sql_a
        assert "beta" in sql_b

    def test_exists_domain_combined_single_exists(self) -> None:
        """Combined helper wraps raw column conditions into single EXISTS."""

        def cond_is_active() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.is_active == True  # noqa: E712

        def cond_name_like() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.description.like("%test%")

        conditions: list[QueryCondition] = [cond_is_active, cond_name_like]
        combined = GroupConditions.exists_domain_combined(conditions)
        sql = str(combined().compile(compile_kwargs={"literal_binds": True}))
        assert "EXISTS" in sql
        assert sql.count("EXISTS") == 1

    def test_exists_domain_combined_returns_column_element(self) -> None:
        conditions: list[QueryCondition] = []
        combined = GroupConditions.exists_domain_combined(conditions)
        result = combined()
        assert isinstance(result, sa.sql.expression.ColumnElement)


class TestGroupOrdersDomainNested:
    """Tests for Domain nested orders in GroupOrders."""

    def test_by_domain_name_ascending(self) -> None:
        order = GroupOrders.by_domain_name(ascending=True)
        order_str = str(order)
        assert "ASC" in order_str or "asc" in order_str.lower()

    def test_by_domain_name_descending(self) -> None:
        order = GroupOrders.by_domain_name(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_by_domain_name_contains_scalar_subquery(self) -> None:
        order = GroupOrders.by_domain_name(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "domains" in order_str
        assert "SELECT" in order_str.upper()

    def test_by_domain_is_active_ascending(self) -> None:
        order = GroupOrders.by_domain_is_active(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "domains" in order_str
        assert "is_active" in order_str

    def test_by_domain_created_at_ascending(self) -> None:
        order = GroupOrders.by_domain_created_at(ascending=True)
        order_str = str(order.compile(compile_kwargs={"literal_binds": True}))
        assert "domains" in order_str
        assert "created_at" in order_str

    def test_by_domain_created_at_descending(self) -> None:
        order = GroupOrders.by_domain_created_at(ascending=False)
        order_str = str(order)
        assert "DESC" in order_str or "desc" in order_str.lower()

    def test_scalar_subquery_returns_clause_element(self) -> None:
        order = GroupOrders.by_domain_name(ascending=True)
        assert isinstance(order, sa.sql.ClauseElement)


class TestGroupNestedSearchIntegration:
    """DB integration tests: nested filter/order applied via GroupDBSource.search_projects."""

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
    ) -> GroupDBSource:
        return GroupDBSource(db=db_with_cleanup)

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
                group = GroupRow(
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

    @pytest.mark.asyncio
    async def test_search_projects_with_domain_is_active_filter(
        self,
        group_db_source: GroupDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """search_projects with by_domain_is_active(True) returns only projects in active domains."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[GroupConditions.by_domain_is_active(True)],
            orders=[],
        )
        result = await group_db_source.search_projects(querier)

        assert result.total_count == 1
        active_domain = [d for d, _ in two_domains_with_projects.items() if "active-dom" in d][0]
        assert result.items[0].id == two_domains_with_projects[active_domain][0]

    @pytest.mark.asyncio
    async def test_search_projects_with_domain_description_contains_filter(
        self,
        group_db_source: GroupDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """search_projects with by_domain_description_contains filters by domain description."""
        spec = StringMatchSpec(value="Research", case_insensitive=True, negated=False)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[GroupConditions.by_domain_description_contains(spec)],
            orders=[],
        )
        result = await group_db_source.search_projects(querier)

        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_projects_with_domain_description_negated_filter(
        self,
        group_db_source: GroupDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """Negated domain description filter excludes matching projects."""
        spec = StringMatchSpec(value="Research", case_insensitive=True, negated=True)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[GroupConditions.by_domain_description_contains(spec)],
            orders=[],
        )
        result = await group_db_source.search_projects(querier)

        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_search_projects_ordered_by_domain_name(
        self,
        group_db_source: GroupDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """search_projects with by_domain_name order sorts by correlated domain name."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[],
            orders=[GroupOrders.by_domain_name(ascending=True)],
        )
        result = await group_db_source.search_projects(querier)

        assert result.total_count == 2
        domain_names = sorted(two_domains_with_projects.keys())
        assert result.items[0].id == two_domains_with_projects[domain_names[0]][0]
        assert result.items[1].id == two_domains_with_projects[domain_names[1]][0]

    @pytest.mark.asyncio
    async def test_search_projects_combined_domain_filter_and_order(
        self,
        group_db_source: GroupDBSource,
        two_domains_with_projects: dict[str, list[uuid.UUID]],
    ) -> None:
        """Combining nested filter + nested order in single search call."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[GroupConditions.by_domain_is_active(True)],
            orders=[GroupOrders.by_domain_name(ascending=True)],
        )
        result = await group_db_source.search_projects(querier)

        assert result.total_count == 1
