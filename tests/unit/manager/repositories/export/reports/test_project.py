"""Tests for project export report definition."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.export.adapter import ExportAdapter
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForProjectRow,
    ScalingGroupOpts,
    ScalingGroupRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.export import (
    ExportFieldDef,
    JoinDef,
    execute_streaming_export,
)
from ai.backend.manager.repositories.export.reports.project import (
    CONTAINER_REGISTRY_JOIN,
    CONTAINER_REGISTRY_JOINS,
    PROJECT_FIELDS,
    PROJECT_REPORT,
    RESOURCE_POLICY_JOIN,
    SCALING_GROUP_FOR_PROJECT_JOIN,
    SCALING_GROUP_JOIN,
    SCALING_GROUP_JOINS,
    _serialize_json,
)
from ai.backend.testutils.db import with_tables


class TestProjectReportDefinition:
    """Tests for PROJECT_REPORT definition."""

    def test_report_key(self) -> None:
        """Report key should be 'projects'."""
        assert PROJECT_REPORT.report_key == "projects"

    def test_report_name(self) -> None:
        """Report name should be 'Projects'."""
        assert PROJECT_REPORT.name == "Projects"

    def test_select_from_is_group_table(self) -> None:
        """select_from should be GroupRow table."""
        assert PROJECT_REPORT.select_from is GroupRow.__table__

    def test_total_field_count(self) -> None:
        """Should have 27 fields total."""
        assert len(PROJECT_REPORT.fields) == 27


class TestProjectFieldDefinitions:
    """Tests for PROJECT_FIELDS definitions."""

    @pytest.fixture
    def field_keys(self) -> set[str]:
        """All field keys in PROJECT_FIELDS."""
        return {f.key for f in PROJECT_FIELDS}

    def test_basic_fields_exist(self, field_keys: set[str]) -> None:
        """Basic fields without joins should exist."""
        basic_keys = {
            "id",
            "name",
            "description",
            "domain_name",
            "is_active",
            "total_resource_slots",
            "created_at",
            "modified_at",
        }
        assert basic_keys.issubset(field_keys)

    def test_vfolder_hosts_field_exists(self, field_keys: set[str]) -> None:
        """allowed_vfolder_hosts field should exist."""
        assert "allowed_vfolder_hosts" in field_keys

    def test_resource_policy_fields_exist(self, field_keys: set[str]) -> None:
        """Resource policy fields should exist."""
        rp_keys = {
            "resource_policy_name",
            "resource_policy_max_vfolder_count",
            "resource_policy_max_quota_scope_size",
            "resource_policy_max_network_count",
            "resource_policy_created_at",
        }
        assert rp_keys.issubset(field_keys)

    def test_scaling_group_fields_exist(self, field_keys: set[str]) -> None:
        """Scaling group fields should exist."""
        sg_keys = {
            "scaling_group_name",
            "scaling_group_description",
            "scaling_group_is_active",
            "scaling_group_is_public",
            "scaling_group_driver",
            "scaling_group_scheduler",
            "scaling_group_created_at",
        }
        assert sg_keys.issubset(field_keys)

    def test_container_registry_fields_exist(self, field_keys: set[str]) -> None:
        """Container registry fields should exist."""
        cr_keys = {
            "container_registry_id",
            "container_registry_url",
            "container_registry_name",
            "container_registry_type",
            "container_registry_project",
            "container_registry_is_global",
        }
        assert cr_keys.issubset(field_keys)


class TestJoinDefinitions:
    """Tests for JOIN definitions."""

    def test_resource_policy_join_table(self) -> None:
        """Resource policy JOIN should use ProjectResourcePolicyRow table."""
        assert RESOURCE_POLICY_JOIN.table is ProjectResourcePolicyRow.__table__

    def test_scaling_group_joins_count(self) -> None:
        """Scaling group should have 2 JOINs."""
        assert len(SCALING_GROUP_JOINS) == 2
        assert SCALING_GROUP_FOR_PROJECT_JOIN in SCALING_GROUP_JOINS
        assert SCALING_GROUP_JOIN in SCALING_GROUP_JOINS

    def test_scaling_group_for_project_join_table(self) -> None:
        """ScalingGroupForProject JOIN should use correct table."""
        assert SCALING_GROUP_FOR_PROJECT_JOIN.table is ScalingGroupForProjectRow.__table__

    def test_scaling_group_join_table(self) -> None:
        """ScalingGroup JOIN should use correct table."""
        assert SCALING_GROUP_JOIN.table is ScalingGroupRow.__table__

    def test_container_registry_joins_count(self) -> None:
        """Container registry should have 1 JOIN (with EXISTS subquery for associations)."""
        assert len(CONTAINER_REGISTRY_JOINS) == 1
        assert CONTAINER_REGISTRY_JOIN in CONTAINER_REGISTRY_JOINS

    def test_container_registry_join_table(self) -> None:
        """Container registry JOIN should use correct table."""
        assert CONTAINER_REGISTRY_JOIN.table is ContainerRegistryRow.__table__


class TestFieldJoinAssignments:
    """Tests for field-join assignments."""

    @pytest.fixture
    def fields_by_key(self) -> dict[str, ExportFieldDef]:
        """Map of field key to field definition."""
        return {f.key: f for f in PROJECT_FIELDS}

    def test_basic_fields_have_no_joins(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """Basic fields should not have joins."""
        basic_keys = ["id", "name", "description", "domain_name", "is_active"]
        for key in basic_keys:
            field = fields_by_key[key]
            assert field.joins is None

    def test_resource_policy_name_has_join(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """resource_policy_name requires RESOURCE_POLICY_JOIN."""
        field = fields_by_key["resource_policy_name"]
        assert field.joins is not None
        assert RESOURCE_POLICY_JOIN in field.joins
        assert len(field.joins) == 1

    def test_resource_policy_detail_fields_have_join(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Resource policy detail fields should have RESOURCE_POLICY_JOIN."""
        rp_detail_keys = [
            "resource_policy_max_vfolder_count",
            "resource_policy_max_quota_scope_size",
            "resource_policy_max_network_count",
            "resource_policy_created_at",
        ]
        for key in rp_detail_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert RESOURCE_POLICY_JOIN in field.joins
            assert len(field.joins) == 1

    def test_scaling_group_fields_have_joins(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Scaling group fields should have SCALING_GROUP_JOINS."""
        sg_keys = [
            "scaling_group_name",
            "scaling_group_description",
            "scaling_group_is_active",
            "scaling_group_is_public",
            "scaling_group_driver",
            "scaling_group_scheduler",
            "scaling_group_created_at",
        ]
        for key in sg_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert field.joins == SCALING_GROUP_JOINS
            assert len(field.joins) == 2

    def test_container_registry_fields_have_joins(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Container registry fields should have CONTAINER_REGISTRY_JOINS."""
        cr_keys = [
            "container_registry_id",
            "container_registry_url",
            "container_registry_name",
            "container_registry_type",
            "container_registry_project",
            "container_registry_is_global",
        ]
        for key in cr_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert field.joins == CONTAINER_REGISTRY_JOINS
            assert len(field.joins) == 1


class TestBuildProjectQueryWithRealReport:
    """Integration tests for build_project_query with PROJECT_REPORT."""

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        """Create ExportAdapter instance."""
        return ExportAdapter()

    def test_basic_fields_no_joins(self, adapter: ExportAdapter) -> None:
        """Selecting only basic fields should not add JOINs."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "name", "domain_name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        # Should be the base table, not a Join
        assert query.select_from is GroupRow.__table__

    def test_resource_policy_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting resource policy fields should add 1 JOIN."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "name", "resource_policy_max_vfolder_count"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "project_resource_policies" in compiled
        # Scaling group and container registry tables should not be joined
        assert "sgroups_for_groups" not in compiled
        assert "container_registries" not in compiled

    def test_scaling_group_fields_add_two_joins(self, adapter: ExportAdapter) -> None:
        """Selecting scaling group fields should add 2 JOINs."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "name", "scaling_group_name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "sgroups_for_groups" in compiled
        assert "scaling_groups" in compiled

    def test_container_registry_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting container registry fields should add 1 JOIN (with EXISTS subquery)."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "name", "container_registry_url"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "container_registries" in compiled
        # Association table is referenced in EXISTS subquery, not as a direct JOIN
        assert compiled.count("LEFT OUTER JOIN") == 1

    def test_all_join_fields_add_all_joins(self, adapter: ExportAdapter) -> None:
        """Selecting all join fields should add all JOINs (4 total)."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=[
                "id",
                "name",
                "resource_policy_max_vfolder_count",
                "scaling_group_name",
                "container_registry_url",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # 4 LEFT OUTER JOINs: 1 (resource_policy) + 2 (scaling_group) + 1 (container_registry)
        assert "project_resource_policies" in compiled
        assert "sgroups_for_groups" in compiled
        assert "scaling_groups" in compiled
        assert "container_registries" in compiled

    def test_all_fields_selected_when_none_specified(self, adapter: ExportAdapter) -> None:
        """None for fields should select all 27 fields."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=None,
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        assert len(query.fields) == 27

    def test_multiple_fields_from_same_join_deduplicate(self, adapter: ExportAdapter) -> None:
        """Multiple fields from same join should not duplicate JOINs."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=[
                "id",
                "scaling_group_name",
                "scaling_group_description",
                "scaling_group_is_active",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # Should have exactly 2 JOINs for scaling group, not 6
        assert compiled.count("LEFT OUTER JOIN") == 2


class TestProjectQuerySQLGenerationForBugReproduction:
    """Tests that reproduce the reported bug:
    /func/export/projects/csv returns empty results when scaling_group_name
    AND container_registry_* fields are selected simultaneously.

    Key invariants:
    1. Each join table must appear exactly once in the FROM clause
    2. All joins must be LEFT OUTER JOINs (not INNER JOINs)
    3. The total JOIN count must be exactly the number of unique join tables
    """

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        """Create ExportAdapter instance."""
        return ExportAdapter()

    def test_scaling_group_and_container_registry_combined_join_count(
        self, adapter: ExportAdapter
    ) -> None:
        """Combining scaling_group and container_registry fields must produce exactly 3 JOINs.

        2 JOINs for scaling group + 1 JOIN for container registry (with EXISTS subquery).
        """
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "scaling_group_name", "container_registry_id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # 2 JOINs for scaling group (sgroups_for_groups + scaling_groups)
        # 1 JOIN for container registry (with EXISTS subquery for associations)
        assert compiled.count("LEFT OUTER JOIN") == 3

    def test_full_field_combination_that_triggers_bug_join_count(
        self, adapter: ExportAdapter
    ) -> None:
        """The exact field combination reported to cause empty results must produce exactly 4 JOINs.

        Fields: name, domain_name, description, created_at, is_active, total_resource_slots,
                resource_policy_name, allowed_vfolder_hosts, scaling_group_name,
                container_registry_id, container_registry_url, container_registry_name,
                container_registry_type, container_registry_project, container_registry_is_global, id
        Expected joins:
          1. project_resource_policies (N:1 for resource_policy_name)
          2. sgroups_for_groups (1:N step 1 for scaling_group_name)
          3. scaling_groups (1:N step 2 for scaling_group_name)
          4. container_registries (1:N with EXISTS subquery for container_registry_*)
        """
        bug_reproduction_fields = [
            "name",
            "domain_name",
            "description",
            "created_at",
            "is_active",
            "total_resource_slots",
            "resource_policy_name",
            "allowed_vfolder_hosts",
            "scaling_group_name",
            "container_registry_id",
            "container_registry_url",
            "container_registry_name",
            "container_registry_type",
            "container_registry_project",
            "container_registry_is_global",
            "id",
        ]
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=bug_reproduction_fields,
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # Exactly 4 JOINs: 1 (resource_policy) + 2 (scaling_group) + 1 (container_registry)
        assert compiled.count("LEFT OUTER JOIN") == 4

    def test_all_joins_are_left_outer_not_inner(self, adapter: ExportAdapter) -> None:
        """All generated JOINs must be LEFT OUTER JOINs, never INNER JOINs.

        If any JOIN becomes INNER JOIN, projects without scaling groups or
        container registries would be filtered out, causing empty results.
        """
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=[
                "id",
                "name",
                "resource_policy_name",
                "scaling_group_name",
                "container_registry_id",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # Must have LEFT OUTER JOINs only
        assert "LEFT OUTER JOIN" in compiled
        # Must NOT have plain INNER JOINs (which would appear as just "JOIN" without "LEFT OUTER")
        # Strip all "LEFT OUTER JOIN" occurrences and check no bare "JOIN" remains
        compiled_without_left_outer = compiled.replace("LEFT OUTER JOIN", "")
        assert "JOIN" not in compiled_without_left_outer

    def test_no_duplicate_table_references_in_from_clause(self, adapter: ExportAdapter) -> None:
        """Each joined table must appear exactly once as a JOIN target in the FROM clause.

        Counts "LEFT OUTER JOIN <table>" occurrences to detect if SQLAlchemy duplicates
        any join. If the same table is joined twice, it would appear as
        "LEFT OUTER JOIN table_name" twice, potentially causing Cartesian products.
        """
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=[
                "id",
                "scaling_group_name",
                "container_registry_id",
                "container_registry_url",
                "container_registry_name",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # Each joined table must appear exactly once as a LEFT OUTER JOIN target.
        for table_name in [
            "sgroups_for_groups",
            "scaling_groups",
            "container_registries",
        ]:
            join_occurrences = compiled.count(f"LEFT OUTER JOIN {table_name}")
            assert join_occurrences == 1, (
                f"Table '{table_name}' appears as JOIN target {join_occurrences} times "
                f"(expected exactly 1). Duplicate join would cause Cartesian product.\n"
                f"Full FROM SQL:\n{compiled}"
            )

    def test_full_select_statement_no_implicit_from_additions(self, adapter: ExportAdapter) -> None:
        """The full SELECT...FROM statement must not add implicit FROM entries.

        When sa.select(*columns) includes ORM InstrumentedAttributes from joined tables,
        SQLAlchemy could potentially add those tables as implicit FROM clauses in addition
        to the explicit join chain. This would create cross joins (INNER JOINs) with the
        raw tables, filtering rows where joins produce no match.

        This test verifies that the complete SQL uses ONLY the explicit join chain.
        """
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=[
                "id",
                "name",
                "resource_policy_name",
                "scaling_group_name",
                "container_registry_id",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        # Simulate what execute_streaming_export does
        columns = [f.column for f in query.fields]
        full_select = sa.select(*columns).select_from(query.select_from)
        compiled = str(full_select.compile(compile_kwargs={"literal_binds": True}))

        # The total JOIN count in the full SELECT must match the FROM clause alone
        from_clause_compiled = str(
            query.select_from.compile(compile_kwargs={"literal_binds": True})
        )
        expected_join_count = from_clause_compiled.count("LEFT OUTER JOIN")
        actual_join_count = compiled.count("LEFT OUTER JOIN")

        assert actual_join_count == expected_join_count, (
            f"Full SELECT has {actual_join_count} LEFT OUTER JOINs "
            f"but FROM clause alone has {expected_join_count}. "
            f"SQLAlchemy may have added implicit FROM entries from ORM attributes.\n"
            f"Full SELECT SQL:\n{compiled}"
        )

        # Verify no raw table references appear outside the join chain
        # (which would indicate implicit FROM / cross join additions)
        for table_name in [
            "sgroups_for_groups",
            "scaling_groups",
            "container_registries",
        ]:
            join_occurrences = compiled.count(f"LEFT OUTER JOIN {table_name}")
            assert join_occurrences == 1, (
                f"Table '{table_name}' appears as JOIN target {join_occurrences} times "
                f"in full SELECT (expected exactly 1).\n"
                f"Full SELECT SQL:\n{compiled}"
            )

    def test_multiple_container_registry_fields_do_not_multiply_joins(
        self, adapter: ExportAdapter
    ) -> None:
        """Selecting multiple container_registry_* fields must not multiply the JOIN count.

        6 container_registry_* fields all share the same CONTAINER_REGISTRY_JOINS tuple.
        Selecting all 6 should still result in exactly 1 JOIN (deduplicated), not 6.
        """
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=[
                "id",
                "container_registry_id",
                "container_registry_url",
                "container_registry_name",
                "container_registry_type",
                "container_registry_project",
                "container_registry_is_global",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # Exactly 1 JOIN regardless of how many container_registry_* fields are selected
        assert compiled.count("LEFT OUTER JOIN") == 1

    def test_join_order_maintains_dependency_for_scaling_group(
        self, adapter: ExportAdapter
    ) -> None:
        """sgroups_for_groups must appear before scaling_groups in the JOIN chain.

        SCALING_GROUP_JOIN depends on sgroups_for_groups already being joined,
        because its condition references ScalingGroupForProjectRow.scaling_group.
        """
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "scaling_group_name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        sg_for_project_pos = compiled.index("sgroups_for_groups")
        sg_pos = compiled.index("scaling_groups")
        assert sg_for_project_pos < sg_pos, (
            "sgroups_for_groups must be joined before scaling_groups, "
            f"but got: sgroups_for_groups at {sg_for_project_pos}, scaling_groups at {sg_pos}"
        )

    def test_container_registry_join_includes_global_condition(
        self, adapter: ExportAdapter
    ) -> None:
        """Container registry JOIN must include is_global condition for global registries.

        The JOIN condition uses OR: is_global=true OR EXISTS(assoc subquery).
        This ensures global registries appear for all projects without explicit association.
        """
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "container_registry_id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "container_registries.is_global" in compiled
        assert "EXISTS" in compiled.upper()
        assert "association_container_registries_groups" in compiled


class TestJoinDefIdentityAndHashing:
    """Tests for JoinDef hash and equality behavior with SQLAlchemy objects.

    JoinDef uses @dataclass(frozen=True), which auto-generates __hash__ and __eq__
    based on (table, condition). Since both are SQLAlchemy objects that override __eq__
    to return ColumnElement (not bool), there is a risk of incorrect hashing/equality.

    These tests verify that the deduplication in _collect_joins works correctly.
    """

    def test_same_joindef_object_detected_as_duplicate_in_set(self) -> None:
        """The same JoinDef object (same Python reference) must be detected as a duplicate.

        This is the core deduplication requirement: module-level constants like
        SCALING_GROUP_FOR_PROJECT_JOIN are the same Python object across all fields
        that reference SCALING_GROUP_JOINS, so set deduplication must work.
        """
        seen: set[JoinDef] = set()
        seen.add(SCALING_GROUP_FOR_PROJECT_JOIN)
        # Adding the same object again must not increase size
        seen.add(SCALING_GROUP_FOR_PROJECT_JOIN)
        assert len(seen) == 1

    def test_different_joindef_objects_from_same_module_constants_are_deduplicated(
        self,
    ) -> None:
        """All fields referencing SCALING_GROUP_JOINS share the same JoinDef instances.

        The adapter's _collect_joins must correctly deduplicate them.
        This directly tests the identity-based deduplication assumption.
        """
        adapter = ExportAdapter()
        # Build two separate fields both using SCALING_GROUP_JOINS
        # scaling_group_name, scaling_group_description, scaling_group_is_active all
        # reference the same SCALING_GROUP_JOINS tuple → same JoinDef objects
        fields_map = {f.key: f for f in PROJECT_REPORT.fields}
        selected_fields = [
            fields_map["scaling_group_name"],
            fields_map["scaling_group_description"],
            fields_map["scaling_group_is_active"],
        ]

        joins = adapter._collect_joins(selected_fields)
        # Despite 3 fields each having 2 joins, the result must be exactly 2 (deduplicated)
        assert len(joins) == 2
        assert SCALING_GROUP_FOR_PROJECT_JOIN in joins
        assert SCALING_GROUP_JOIN in joins

    def test_all_four_joins_collected_for_full_field_combination(self) -> None:
        """When resource_policy + scaling_group + container_registry fields are all selected,
        exactly 4 unique JoinDef objects must be collected.
        """
        adapter = ExportAdapter()
        fields_map = {f.key: f for f in PROJECT_REPORT.fields}
        selected_fields = [
            fields_map["resource_policy_name"],
            fields_map["scaling_group_name"],
            fields_map["container_registry_id"],
            fields_map["container_registry_url"],  # same joins as container_registry_id
        ]

        joins = adapter._collect_joins(selected_fields)
        assert len(joins) == 4, (
            f"Expected 4 unique joins "
            f"(1 resource_policy + 2 scaling_group + 1 container_registry), "
            f"got {len(joins)}: {joins}"
        )


@dataclass(frozen=True)
class _ProjectWithSgAndRegistry:
    project_id: uuid.UUID
    domain_name: str
    sg_name: str
    registry_id: uuid.UUID


@dataclass(frozen=True)
class _ProjectWithMixedRegistries:
    project_id: uuid.UUID
    global_registry_id: uuid.UUID
    scoped_registry_id: uuid.UUID


class TestProjectExportExecuteStreamingDB:
    """DB-level integration tests for execute_streaming_export with project data."""

    @pytest.fixture
    async def db_engine(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Engine with all required tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                GroupRow,
                ScalingGroupRow,
                ScalingGroupForProjectRow,
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def project_with_sg_and_registry(
        self,
        db_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[_ProjectWithSgAndRegistry, None]:
        """Create a project associated with a scaling group and a container registry."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()
        sg_name = f"test-sg-{uuid.uuid4().hex[:8]}"
        registry_id = uuid.uuid4()

        async with db_engine.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.flush()

            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=project_id,
                    name="test-project",
                    domain_name=domain_name,
                    resource_policy=policy_name,
                )
            )
            await db_sess.flush()

            db_sess.add(
                ScalingGroupRow(
                    name=sg_name,
                    description="",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                    wsproxy_addr=None,
                )
            )
            await db_sess.flush()

            db_sess.add(ScalingGroupForProjectRow(scaling_group=sg_name, group=project_id))
            await db_sess.flush()

            db_sess.add(
                ContainerRegistryRow(
                    id=registry_id,
                    url="https://registry.example.com",
                    registry_name="test-registry",
                    type=ContainerRegistryType.DOCKER,
                    is_global=False,
                )
            )
            await db_sess.flush()

            db_sess.add(
                AssociationContainerRegistriesGroupsRow(
                    id=uuid.uuid4(),
                    registry_id=registry_id,
                    group_id=project_id,
                )
            )
            await db_sess.commit()

        yield _ProjectWithSgAndRegistry(
            project_id=project_id,
            domain_name=domain_name,
            sg_name=sg_name,
            registry_id=registry_id,
        )

    async def test_basic_fields_return_project_row(
        self,
        db_engine: ExtendedAsyncSAEngine,
        project_with_sg_and_registry: _ProjectWithSgAndRegistry,
    ) -> None:
        """SELECT with basic fields only should return the project row (baseline)."""
        adapter = ExportAdapter()
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "name", "domain_name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        assert len(rows) == 1
        assert str(rows[0][0]) == str(project_with_sg_and_registry.project_id)

    async def test_container_registry_join_returns_rows_not_empty(
        self,
        db_engine: ExtendedAsyncSAEngine,
        project_with_sg_and_registry: _ProjectWithSgAndRegistry,
    ) -> None:
        """SELECT with container_registry_* fields must NOT return empty results."""
        adapter = ExportAdapter()
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "name", "container_registry_id", "container_registry_url"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        assert len(rows) >= 1
        assert str(rows[0][2]) == str(project_with_sg_and_registry.registry_id)

    async def test_scaling_group_and_container_registry_combined_returns_rows(
        self,
        db_engine: ExtendedAsyncSAEngine,
        project_with_sg_and_registry: _ProjectWithSgAndRegistry,
    ) -> None:
        """Both scaling_group and container_registry fields selected together must return rows."""
        adapter = ExportAdapter()
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=[
                "name",
                "domain_name",
                "description",
                "created_at",
                "is_active",
                "total_resource_slots",
                "resource_policy_name",
                "allowed_vfolder_hosts",
                "scaling_group_name",
                "container_registry_id",
                "container_registry_url",
                "container_registry_name",
                "container_registry_type",
                "container_registry_project",
                "container_registry_is_global",
                "id",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        assert len(rows) >= 1
        assert str(rows[0][15]) == str(project_with_sg_and_registry.project_id)

    async def test_project_without_registry_returns_row_with_null_registry_fields(
        self,
        db_engine: ExtendedAsyncSAEngine,
        project_with_sg_and_registry: _ProjectWithSgAndRegistry,
    ) -> None:
        """A project with no registry must still appear (with NULL registry columns)."""
        policy_name2 = f"test-policy2-{uuid.uuid4().hex[:8]}"
        project_id2 = uuid.uuid4()

        async with db_engine.begin_session() as db_sess:
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name2,
                    max_vfolder_count=5,
                    max_quota_scope_size=-1,
                    max_network_count=5,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=project_id2,
                    name="project-no-registry",
                    domain_name=project_with_sg_and_registry.domain_name,
                    resource_policy=policy_name2,
                )
            )
            await db_sess.commit()

        adapter = ExportAdapter()
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "name", "container_registry_id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        assert len(rows) == 2
        row_ids = {str(r[0]) for r in rows}
        assert str(project_id2) in row_ids


class TestGlobalContainerRegistryExport:
    """Tests that global container registries appear in project export (BA-4708)."""

    @pytest.fixture
    async def db_engine(
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
                ScalingGroupForProjectRow,
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def project_with_mixed_registries(
        self,
        db_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[_ProjectWithMixedRegistries, None]:
        """Create a project with one global registry and one scoped (associated) registry."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()
        global_registry_id = uuid.uuid4()
        scoped_registry_id = uuid.uuid4()

        async with db_engine.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            await db_sess.flush()
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()
            db_sess.add(
                GroupRow(
                    id=project_id,
                    name="test-project",
                    domain_name=domain_name,
                    resource_policy=policy_name,
                )
            )
            await db_sess.flush()
            db_sess.add(
                ContainerRegistryRow(
                    id=global_registry_id,
                    url="https://global-registry.example.com",
                    registry_name="global-registry",
                    type=ContainerRegistryType.DOCKER,
                    is_global=True,
                )
            )
            db_sess.add(
                ContainerRegistryRow(
                    id=scoped_registry_id,
                    url="https://scoped-registry.example.com",
                    registry_name="scoped-registry",
                    type=ContainerRegistryType.DOCKER,
                    is_global=False,
                )
            )
            await db_sess.flush()
            db_sess.add(
                AssociationContainerRegistriesGroupsRow(
                    id=uuid.uuid4(),
                    registry_id=scoped_registry_id,
                    group_id=project_id,
                )
            )
            await db_sess.commit()

        yield _ProjectWithMixedRegistries(
            project_id=project_id,
            global_registry_id=global_registry_id,
            scoped_registry_id=scoped_registry_id,
        )

    async def test_global_and_scoped_registries_both_appear(
        self,
        db_engine: ExtendedAsyncSAEngine,
        project_with_mixed_registries: _ProjectWithMixedRegistries,
    ) -> None:
        """Both global and scoped registries must appear in project export (BA-4708)."""
        adapter = ExportAdapter()
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "name", "container_registry_id", "container_registry_is_global"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        data = project_with_mixed_registries
        registry_ids = {str(row[2]) for row in rows}
        assert len(rows) == 2
        assert str(data.global_registry_id) in registry_ids
        assert str(data.scoped_registry_id) in registry_ids


class TestSerializeJson:
    """Unit tests for _serialize_json helper function.

    Regression tests for TypeError: Object of type Decimal is not JSON serializable,
    which caused the CSV export to return empty results when total_resource_slots
    (ResourceSlot with Decimal values) was included in the export fields.
    """

    def test_resource_slot_with_decimal_values_serializes_without_error(self) -> None:
        """ResourceSlot containing Decimal values must serialize to a JSON string.

        This is the direct regression test for the reported bug.
        Before the fix, this raised: TypeError: Object of type Decimal is not JSON serializable
        """
        slot = ResourceSlot({"cpu": "2", "mem": "4096"})
        result = _serialize_json(slot)
        assert result != ""
        parsed = json.loads(result)
        assert parsed["cpu"] == "2"
        assert parsed["mem"] == "4096"

    def test_empty_resource_slot_returns_empty_string(self) -> None:
        """Empty ResourceSlot (falsy) must return empty string, not crash."""
        slot = ResourceSlot()
        result = _serialize_json(slot)
        assert result == ""

    def test_set_values_are_sorted_to_list(self) -> None:
        """set values must be converted to sorted lists for stable JSON output."""
        result = _serialize_json({"key": {"b", "a", "c"}})
        parsed = json.loads(result)
        assert parsed["key"] == ["a", "b", "c"]

    def test_nested_dict_with_decimal_serializes_correctly(self) -> None:
        """Nested dict values containing Decimal must be recursively converted."""
        result = _serialize_json({"nested": {"amount": Decimal("1.5")}})
        parsed = json.loads(result)
        assert parsed["nested"]["amount"] == "1.5"
