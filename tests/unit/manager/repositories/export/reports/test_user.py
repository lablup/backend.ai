"""Tests for user export report definition."""

from __future__ import annotations

import pytest

from ai.backend.manager.api.export.adapter import ExportAdapter
from ai.backend.manager.models.group.row import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.export import ExportFieldDef
from ai.backend.manager.repositories.export.reports.user import (
    ASSOC_GROUP_USER_JOIN,
    MAIN_KEYPAIR_JOIN,
    PROJECT_JOIN,
    PROJECT_JOINS,
    USER_FIELDS,
    USER_REPORT,
    USER_RESOURCE_POLICY_JOIN,
)


class TestUserReportDefinition:
    """Tests for USER_REPORT definition."""

    def test_report_key(self) -> None:
        """Report key should be 'users'."""
        assert USER_REPORT.report_key == "users"

    def test_report_name(self) -> None:
        """Report name should be 'Users'."""
        assert USER_REPORT.name == "Users"

    def test_select_from_is_user_table(self) -> None:
        """select_from should be UserRow table."""
        assert USER_REPORT.select_from is UserRow.__table__

    def test_total_field_count(self) -> None:
        """Should have 25 fields total (9 basic + 16 new)."""
        assert len(USER_REPORT.fields) == 25


class TestUserFieldDefinitions:
    """Tests for USER_FIELDS definitions."""

    @pytest.fixture
    def field_keys(self) -> set[str]:
        """All field keys in USER_FIELDS."""
        return {f.key for f in USER_FIELDS}

    def test_basic_fields_exist(self, field_keys: set[str]) -> None:
        """Basic fields without joins should exist."""
        basic_keys = {
            "uuid",
            "username",
            "email",
            "full_name",
            "domain_name",
            "role",
            "status",
            "created_at",
            "modified_at",
        }
        assert basic_keys.issubset(field_keys)

    def test_resource_policy_fields_exist(self, field_keys: set[str]) -> None:
        """Resource policy fields should exist."""
        rp_keys = {
            "resource_policy_name",
            "resource_policy_created_at",
            "resource_policy_max_vfolder_count",
            "resource_policy_max_quota_scope_size",
            "resource_policy_max_session_count_per_model",
            "resource_policy_max_customized_image_count",
        }
        assert rp_keys.issubset(field_keys)

    def test_project_fields_exist(self, field_keys: set[str]) -> None:
        """Project fields should exist."""
        project_keys = {
            "project_id",
            "project_name",
            "project_description",
            "project_domain_name",
            "project_is_active",
            "project_created_at",
        }
        assert project_keys.issubset(field_keys)

    def test_main_keypair_fields_exist(self, field_keys: set[str]) -> None:
        """Main keypair fields should exist."""
        keypair_keys = {
            "main_access_key",
            "main_keypair_is_active",
            "main_keypair_created_at",
            "main_keypair_last_used",
        }
        assert keypair_keys.issubset(field_keys)


class TestJoinDefinitions:
    """Tests for JOIN definitions."""

    def test_user_resource_policy_join_table(self) -> None:
        """User resource policy JOIN should use UserResourcePolicyRow table."""
        assert USER_RESOURCE_POLICY_JOIN.table is UserResourcePolicyRow.__table__

    def test_project_joins_count(self) -> None:
        """Project should have 2 JOINs (AssocGroupUser + Group)."""
        assert len(PROJECT_JOINS) == 2
        assert ASSOC_GROUP_USER_JOIN in PROJECT_JOINS
        assert PROJECT_JOIN in PROJECT_JOINS

    def test_assoc_group_user_join_table(self) -> None:
        """AssocGroupUser JOIN should use correct table."""
        assert ASSOC_GROUP_USER_JOIN.table is AssocGroupUserRow.__table__

    def test_project_join_table(self) -> None:
        """Project JOIN should use GroupRow table."""
        assert PROJECT_JOIN.table is GroupRow.__table__

    def test_main_keypair_join_table(self) -> None:
        """Main keypair JOIN should use KeyPairRow table."""
        assert MAIN_KEYPAIR_JOIN.table is KeyPairRow.__table__


class TestFieldJoinAssignments:
    """Tests for field-join assignments."""

    @pytest.fixture
    def fields_by_key(self) -> dict[str, ExportFieldDef]:
        """Map of field key to field definition."""
        return {f.key: f for f in USER_FIELDS}

    def test_basic_fields_have_no_joins(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """Basic fields should not have joins."""
        basic_keys = ["uuid", "username", "email", "full_name", "domain_name"]
        for key in basic_keys:
            field = fields_by_key[key]
            assert field.joins is None

    def test_resource_policy_name_has_join(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """resource_policy_name requires USER_RESOURCE_POLICY_JOIN."""
        field = fields_by_key["resource_policy_name"]
        assert field.joins is not None
        assert USER_RESOURCE_POLICY_JOIN in field.joins
        assert len(field.joins) == 1

    def test_main_access_key_has_no_join(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """main_access_key is in UserRow, so no join needed."""
        field = fields_by_key["main_access_key"]
        assert field.joins is None

    def test_resource_policy_detail_fields_have_join(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Resource policy detail fields should have USER_RESOURCE_POLICY_JOIN."""
        rp_detail_keys = [
            "resource_policy_created_at",
            "resource_policy_max_vfolder_count",
            "resource_policy_max_quota_scope_size",
            "resource_policy_max_session_count_per_model",
            "resource_policy_max_customized_image_count",
        ]
        for key in rp_detail_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert USER_RESOURCE_POLICY_JOIN in field.joins
            assert len(field.joins) == 1

    def test_project_fields_have_joins(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """Project fields should have PROJECT_JOINS."""
        project_keys = [
            "project_id",
            "project_name",
            "project_description",
            "project_domain_name",
            "project_is_active",
            "project_created_at",
        ]
        for key in project_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert field.joins == PROJECT_JOINS
            assert len(field.joins) == 2

    def test_main_keypair_detail_fields_have_join(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Main keypair detail fields should have MAIN_KEYPAIR_JOIN."""
        keypair_detail_keys = [
            "main_keypair_is_active",
            "main_keypair_created_at",
            "main_keypair_last_used",
        ]
        for key in keypair_detail_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert MAIN_KEYPAIR_JOIN in field.joins
            assert len(field.joins) == 1


class TestBuildUserQueryWithRealReport:
    """Integration tests for build_user_query with USER_REPORT."""

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        """Create ExportAdapter instance."""
        return ExportAdapter()

    def test_basic_fields_no_joins(self, adapter: ExportAdapter) -> None:
        """Selecting only basic fields should not add JOINs."""
        query = adapter.build_user_query(
            report=USER_REPORT,
            fields=["uuid", "username", "email"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        # Should be the base table, not a Join
        assert query.select_from is UserRow.__table__

    def test_resource_policy_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting resource policy fields should add 1 JOIN."""
        query = adapter.build_user_query(
            report=USER_REPORT,
            fields=["uuid", "resource_policy_max_vfolder_count"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "user_resource_policies" in compiled
        # Project and keypair tables should not be joined
        assert "association_groups_users" not in compiled
        assert "keypairs" not in compiled

    def test_project_fields_add_two_joins(self, adapter: ExportAdapter) -> None:
        """Selecting project fields should add 2 JOINs."""
        query = adapter.build_user_query(
            report=USER_REPORT,
            fields=["uuid", "project_name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "association_groups_users" in compiled
        assert "groups" in compiled

    def test_main_keypair_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting main keypair fields should add 1 JOIN."""
        query = adapter.build_user_query(
            report=USER_REPORT,
            fields=["uuid", "main_keypair_is_active"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "keypairs" in compiled

    def test_mixed_fields_add_all_joins(self, adapter: ExportAdapter) -> None:
        """Selecting fields from all categories should add all JOINs."""
        query = adapter.build_user_query(
            report=USER_REPORT,
            fields=[
                "uuid",
                "username",
                "resource_policy_max_vfolder_count",
                "project_name",
                "main_keypair_is_active",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # All 4 join tables should be present
        assert "user_resource_policies" in compiled
        assert "association_groups_users" in compiled
        assert "groups" in compiled
        assert "keypairs" in compiled
