"""Tests for project export report definition."""

from __future__ import annotations

import pytest

from ai.backend.manager.api.export.adapter import ExportAdapter
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow, ScalingGroupRow
from ai.backend.manager.repositories.base.export import ExportFieldDef
from ai.backend.manager.repositories.export.reports.project import (
    CONTAINER_REGISTRY_ASSOC_JOIN,
    CONTAINER_REGISTRY_JOIN,
    CONTAINER_REGISTRY_JOINS,
    PROJECT_FIELDS,
    PROJECT_REPORT,
    RESOURCE_POLICY_JOIN,
    SCALING_GROUP_FOR_PROJECT_JOIN,
    SCALING_GROUP_JOIN,
    SCALING_GROUP_JOINS,
)


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
        """Container registry should have 2 JOINs."""
        assert len(CONTAINER_REGISTRY_JOINS) == 2
        assert CONTAINER_REGISTRY_ASSOC_JOIN in CONTAINER_REGISTRY_JOINS
        assert CONTAINER_REGISTRY_JOIN in CONTAINER_REGISTRY_JOINS

    def test_container_registry_assoc_join_table(self) -> None:
        """Container registry association JOIN should use correct table."""
        assert (
            CONTAINER_REGISTRY_ASSOC_JOIN.table is AssociationContainerRegistriesGroupsRow.__table__
        )

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

    def test_resource_policy_name_has_no_join(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """resource_policy_name is in GroupRow, so no join needed."""
        field = fields_by_key["resource_policy_name"]
        assert field.joins is None

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

    def test_scaling_group_fields_have_joins(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
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

    def test_container_registry_fields_have_joins(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
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
            assert len(field.joins) == 2


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

    def test_container_registry_fields_add_two_joins(self, adapter: ExportAdapter) -> None:
        """Selecting container registry fields should add 2 JOINs."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=["id", "name", "container_registry_url"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "association_container_registries_groups" in compiled
        assert "container_registries" in compiled

    def test_all_join_fields_add_all_joins(self, adapter: ExportAdapter) -> None:
        """Selecting all join fields should add all JOINs (5 total)."""
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
        # All 5 join tables should be present
        assert "project_resource_policies" in compiled
        assert "sgroups_for_groups" in compiled
        assert "scaling_groups" in compiled
        assert "association_container_registries_groups" in compiled
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
