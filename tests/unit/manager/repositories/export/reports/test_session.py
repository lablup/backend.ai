"""Tests for session export report definition."""

from __future__ import annotations

import pytest

from ai.backend.manager.api.export.adapter import ExportAdapter
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.export import ExportFieldDef
from ai.backend.manager.repositories.export.reports.session import (
    KERNEL_JOIN,
    MAIN_KERNEL_JOIN,
    PROJECT_JOIN,
    PROJECT_POLICY_JOINS,
    PROJECT_RESOURCE_POLICY_JOIN,
    SESSION_FIELDS,
    SESSION_REPORT,
    USER_JOIN,
)


class TestSessionReportDefinition:
    """Tests for SESSION_REPORT definition."""

    def test_report_key(self) -> None:
        """Report key should be 'sessions'."""
        assert SESSION_REPORT.report_key == "sessions"

    def test_report_name(self) -> None:
        """Report name should be 'Sessions'."""
        assert SESSION_REPORT.name == "Sessions"

    def test_select_from_is_session_table(self) -> None:
        """select_from should be SessionRow table."""
        assert SESSION_REPORT.select_from is SessionRow.__table__

    def test_total_field_count(self) -> None:
        """Should have 35 fields total (12 basic + 23 new)."""
        assert len(SESSION_REPORT.fields) == 35


class TestSessionFieldDefinitions:
    """Tests for SESSION_FIELDS definitions."""

    @pytest.fixture
    def field_keys(self) -> set[str]:
        """All field keys in SESSION_FIELDS."""
        return {f.key for f in SESSION_FIELDS}

    def test_basic_fields_exist(self, field_keys: set[str]) -> None:
        """Basic fields without joins should exist."""
        basic_keys = {
            "id",
            "name",
            "session_type",
            "domain_name",
            "access_key",
            "status",
            "status_info",
            "scaling_group_name",
            "cluster_size",
            "occupying_slots",
            "created_at",
            "terminated_at",
        }
        assert basic_keys.issubset(field_keys)

    def test_main_kernel_fields_exist(self, field_keys: set[str]) -> None:
        """Main kernel fields should exist."""
        main_kernel_keys = {
            "main_kernel_image",
            "main_kernel_architecture",
            "main_kernel_registry",
            "main_kernel_tag",
        }
        assert main_kernel_keys.issubset(field_keys)

    def test_project_fields_exist(self, field_keys: set[str]) -> None:
        """Project fields should exist."""
        project_keys = {
            "project_name",
            "project_description",
            "project_resource_policy",
            "project_is_active",
            "project_created_at",
        }
        assert project_keys.issubset(field_keys)

    def test_project_policy_fields_exist(self, field_keys: set[str]) -> None:
        """Project policy fields should exist."""
        policy_keys = {
            "project_policy_max_vfolder_count",
            "project_policy_max_quota_scope_size",
            "project_policy_max_network_count",
        }
        assert policy_keys.issubset(field_keys)

    def test_user_fields_exist(self, field_keys: set[str]) -> None:
        """User fields should exist."""
        user_keys = {
            "user_email",
            "user_username",
            "user_full_name",
            "user_role",
        }
        assert user_keys.issubset(field_keys)

    def test_kernel_fields_exist(self, field_keys: set[str]) -> None:
        """Kernel fields should exist."""
        kernel_keys = {
            "kernel_id",
            "kernel_role",
            "kernel_status",
            "kernel_image",
            "kernel_agent",
            "kernel_created_at",
            "kernel_terminated_at",
        }
        assert kernel_keys.issubset(field_keys)


class TestJoinDefinitions:
    """Tests for JOIN definitions."""

    def test_project_join_table(self) -> None:
        """Project JOIN should use GroupRow table."""
        assert PROJECT_JOIN.table is GroupRow.__table__

    def test_project_resource_policy_join_table(self) -> None:
        """Project resource policy JOIN should use ProjectResourcePolicyRow table."""
        assert PROJECT_RESOURCE_POLICY_JOIN.table is ProjectResourcePolicyRow.__table__

    def test_project_policy_joins_count(self) -> None:
        """Project policy should have 2 JOINs."""
        assert len(PROJECT_POLICY_JOINS) == 2
        assert PROJECT_JOIN in PROJECT_POLICY_JOINS
        assert PROJECT_RESOURCE_POLICY_JOIN in PROJECT_POLICY_JOINS

    def test_user_join_table(self) -> None:
        """User JOIN should use UserRow table."""
        assert USER_JOIN.table is UserRow.__table__

    def test_kernel_join_table(self) -> None:
        """Kernel JOIN should use KernelRow table."""
        assert KERNEL_JOIN.table is KernelRow.__table__

    def test_main_kernel_join_table(self) -> None:
        """Main kernel JOIN should use KernelRow table."""
        assert MAIN_KERNEL_JOIN.table is KernelRow.__table__


class TestFieldJoinAssignments:
    """Tests for field-join assignments."""

    @pytest.fixture
    def fields_by_key(self) -> dict[str, ExportFieldDef]:
        """Map of field key to field definition."""
        return {f.key: f for f in SESSION_FIELDS}

    def test_basic_fields_have_no_joins(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Basic fields should not have joins."""
        basic_keys = [
            "id",
            "name",
            "session_type",
            "domain_name",
            "access_key",
            "status",
        ]
        for key in basic_keys:
            field = fields_by_key[key]
            assert field.joins is None

    def test_main_kernel_fields_have_join(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Main kernel fields should have MAIN_KERNEL_JOIN."""
        main_kernel_keys = [
            "main_kernel_image",
            "main_kernel_architecture",
            "main_kernel_registry",
            "main_kernel_tag",
        ]
        for key in main_kernel_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert MAIN_KERNEL_JOIN in field.joins
            assert len(field.joins) == 1

    def test_project_fields_have_join(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Project fields should have PROJECT_JOIN."""
        project_keys = [
            "project_name",
            "project_description",
            "project_resource_policy",
            "project_is_active",
            "project_created_at",
        ]
        for key in project_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert PROJECT_JOIN in field.joins
            assert len(field.joins) == 1

    def test_project_policy_fields_have_joins(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Project policy fields should have PROJECT_POLICY_JOINS."""
        policy_keys = [
            "project_policy_max_vfolder_count",
            "project_policy_max_quota_scope_size",
            "project_policy_max_network_count",
        ]
        for key in policy_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert field.joins == PROJECT_POLICY_JOINS
            assert len(field.joins) == 2

    def test_user_fields_have_join(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """User fields should have USER_JOIN."""
        user_keys = [
            "user_email",
            "user_username",
            "user_full_name",
            "user_role",
        ]
        for key in user_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert USER_JOIN in field.joins
            assert len(field.joins) == 1

    def test_kernel_fields_have_join(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Kernel fields should have KERNEL_JOIN."""
        kernel_keys = [
            "kernel_id",
            "kernel_role",
            "kernel_status",
            "kernel_image",
            "kernel_agent",
            "kernel_created_at",
            "kernel_terminated_at",
        ]
        for key in kernel_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert KERNEL_JOIN in field.joins
            assert len(field.joins) == 1


class TestBuildSessionQueryWithRealReport:
    """Integration tests for build_session_query with SESSION_REPORT."""

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        """Create ExportAdapter instance."""
        return ExportAdapter()

    def test_basic_fields_no_joins(self, adapter: ExportAdapter) -> None:
        """Selecting only basic fields should not add JOINs."""
        query = adapter.build_session_query(
            report=SESSION_REPORT,
            fields=["id", "name", "status"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        # Should be the base table, not a Join
        assert query.select_from is SessionRow.__table__

    def test_main_kernel_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting main kernel fields should add 1 JOIN."""
        query = adapter.build_session_query(
            report=SESSION_REPORT,
            fields=["id", "main_kernel_image"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "kernels" in compiled

    def test_project_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting project fields should add 1 JOIN."""
        query = adapter.build_session_query(
            report=SESSION_REPORT,
            fields=["id", "project_name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "groups" in compiled
        # Project policy should not be joined
        assert "project_resource_policies" not in compiled

    def test_project_policy_fields_add_two_joins(self, adapter: ExportAdapter) -> None:
        """Selecting project policy fields should add 2 JOINs."""
        query = adapter.build_session_query(
            report=SESSION_REPORT,
            fields=["id", "project_policy_max_vfolder_count"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "groups" in compiled
        assert "project_resource_policies" in compiled

    def test_user_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting user fields should add 1 JOIN."""
        query = adapter.build_session_query(
            report=SESSION_REPORT,
            fields=["id", "user_email"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "users" in compiled

    def test_kernel_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting kernel fields should add 1 JOIN."""
        query = adapter.build_session_query(
            report=SESSION_REPORT,
            fields=["id", "kernel_id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "kernels" in compiled

    def test_mixed_fields_add_all_joins(self, adapter: ExportAdapter) -> None:
        """Selecting fields from all categories should add all JOINs."""
        query = adapter.build_session_query(
            report=SESSION_REPORT,
            fields=[
                "id",
                "name",
                "main_kernel_image",
                "project_name",
                "project_policy_max_vfolder_count",
                "user_email",
                "kernel_id",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # All join tables should be present
        assert "groups" in compiled
        assert "project_resource_policies" in compiled
        assert "users" in compiled
        assert "kernels" in compiled
