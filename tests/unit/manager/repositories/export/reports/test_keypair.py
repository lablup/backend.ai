"""Tests for keypair export report definition."""

from __future__ import annotations

import pytest

from ai.backend.manager.api.export.adapter import ExportAdapter
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupForKeypairsRow, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.export import ExportFieldDef
from ai.backend.manager.repositories.export.reports.keypair import (
    KEYPAIR_FIELDS,
    KEYPAIR_REPORT,
    RESOURCE_GROUP_JOIN,
    RESOURCE_GROUP_JOINS,
    RESOURCE_POLICY_JOIN,
    SESSION_JOIN,
    SGROUP_FOR_KEYPAIR_JOIN,
    USER_JOIN,
)


class TestKeypairReportDefinition:
    """Tests for KEYPAIR_REPORT definition."""

    def test_report_key(self) -> None:
        """Report key should be 'keypairs'."""
        assert KEYPAIR_REPORT.report_key == "keypairs"

    def test_report_name(self) -> None:
        """Report name should be 'Keypairs'."""
        assert KEYPAIR_REPORT.name == "Keypairs"

    def test_select_from_is_keypair_table(self) -> None:
        """select_from should be KeyPairRow table."""
        assert KEYPAIR_REPORT.select_from is KeyPairRow.__table__

    def test_total_field_count(self) -> None:
        """Should have 37 fields total (9 basic + 28 new)."""
        assert len(KEYPAIR_REPORT.fields) == 37


class TestKeypairFieldDefinitions:
    """Tests for KEYPAIR_FIELDS definitions."""

    @pytest.fixture
    def field_keys(self) -> set[str]:
        """All field keys in KEYPAIR_FIELDS."""
        return {f.key for f in KEYPAIR_FIELDS}

    def test_basic_fields_exist(self, field_keys: set[str]) -> None:
        """Basic fields without joins should exist."""
        basic_keys = {
            "access_key",
            "user_id",
            "user_uuid",
            "is_active",
            "is_admin",
            "created_at",
            "modified_at",
            "last_used",
            "resource_policy_name",
        }
        assert basic_keys.issubset(field_keys)

    def test_user_fields_exist(self, field_keys: set[str]) -> None:
        """User fields should exist."""
        user_keys = {
            "user_username",
            "user_full_name",
            "user_role",
            "user_status",
            "user_domain_name",
        }
        assert user_keys.issubset(field_keys)

    def test_resource_policy_fields_exist(self, field_keys: set[str]) -> None:
        """Resource policy fields should exist."""
        policy_keys = {
            "resource_policy_created_at",
            "resource_policy_max_concurrent_sessions",
            "resource_policy_max_containers_per_session",
            "resource_policy_idle_timeout",
            "resource_policy_max_session_lifetime",
            "resource_policy_max_pending_session_count",
            "resource_policy_max_pending_session_resource_slots",
            "resource_policy_max_concurrent_sftp_sessions",
        }
        assert policy_keys.issubset(field_keys)

    def test_resource_group_fields_exist(self, field_keys: set[str]) -> None:
        """Resource group fields should exist."""
        rg_keys = {
            "resource_group_name",
            "resource_group_description",
            "resource_group_is_active",
            "resource_group_scheduler",
            "resource_group_wsproxy_addr",
            "resource_group_fair_share_spec",
        }
        assert rg_keys.issubset(field_keys)

    def test_session_fields_exist(self, field_keys: set[str]) -> None:
        """Session fields should exist."""
        session_keys = {
            "session_id",
            "session_name",
            "session_status",
            "session_type",
            "session_domain_name",
            "session_group_id",
            "session_created_at",
            "session_terminated_at",
            "session_requested_slots",
        }
        assert session_keys.issubset(field_keys)


class TestJoinDefinitions:
    """Tests for JOIN definitions."""

    def test_user_join_table(self) -> None:
        """User JOIN should use UserRow table."""
        assert USER_JOIN.table is UserRow.__table__

    def test_resource_policy_join_table(self) -> None:
        """Resource policy JOIN should use KeyPairResourcePolicyRow table."""
        assert RESOURCE_POLICY_JOIN.table is KeyPairResourcePolicyRow.__table__

    def test_resource_group_joins_count(self) -> None:
        """Resource group should have 2 JOINs."""
        assert len(RESOURCE_GROUP_JOINS) == 2
        assert SGROUP_FOR_KEYPAIR_JOIN in RESOURCE_GROUP_JOINS
        assert RESOURCE_GROUP_JOIN in RESOURCE_GROUP_JOINS

    def test_sgroup_for_keypair_join_table(self) -> None:
        """ScalingGroupForKeypairs JOIN should use correct table."""
        assert SGROUP_FOR_KEYPAIR_JOIN.table is ScalingGroupForKeypairsRow.__table__

    def test_resource_group_join_table(self) -> None:
        """Resource group JOIN should use ScalingGroupRow table."""
        assert RESOURCE_GROUP_JOIN.table is ScalingGroupRow.__table__

    def test_session_join_table(self) -> None:
        """Session JOIN should use SessionRow table."""
        assert SESSION_JOIN.table is SessionRow.__table__


class TestFieldJoinAssignments:
    """Tests for field-join assignments."""

    @pytest.fixture
    def fields_by_key(self) -> dict[str, ExportFieldDef]:
        """Map of field key to field definition."""
        return {f.key: f for f in KEYPAIR_FIELDS}

    def test_basic_fields_have_no_joins(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """Basic fields should not have joins."""
        basic_keys = [
            "access_key",
            "user_id",
            "user_uuid",
            "is_active",
            "is_admin",
            "resource_policy_name",
        ]
        for key in basic_keys:
            field = fields_by_key[key]
            assert field.joins is None

    def test_user_fields_have_join(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """User fields should have USER_JOIN."""
        user_keys = [
            "user_username",
            "user_full_name",
            "user_role",
            "user_status",
            "user_domain_name",
        ]
        for key in user_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert USER_JOIN in field.joins
            assert len(field.joins) == 1

    def test_resource_policy_detail_fields_have_join(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Resource policy detail fields should have RESOURCE_POLICY_JOIN."""
        policy_keys = [
            "resource_policy_created_at",
            "resource_policy_max_concurrent_sessions",
            "resource_policy_max_containers_per_session",
            "resource_policy_idle_timeout",
            "resource_policy_max_session_lifetime",
            "resource_policy_max_pending_session_count",
            "resource_policy_max_pending_session_resource_slots",
            "resource_policy_max_concurrent_sftp_sessions",
        ]
        for key in policy_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert RESOURCE_POLICY_JOIN in field.joins
            assert len(field.joins) == 1

    def test_resource_group_fields_have_joins(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Resource group fields should have RESOURCE_GROUP_JOINS."""
        rg_keys = [
            "resource_group_name",
            "resource_group_description",
            "resource_group_is_active",
            "resource_group_scheduler",
            "resource_group_wsproxy_addr",
            "resource_group_fair_share_spec",
        ]
        for key in rg_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert field.joins == RESOURCE_GROUP_JOINS
            assert len(field.joins) == 2

    def test_session_fields_have_join(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """Session fields should have SESSION_JOIN."""
        session_keys = [
            "session_id",
            "session_name",
            "session_status",
            "session_type",
            "session_domain_name",
            "session_group_id",
            "session_created_at",
            "session_terminated_at",
            "session_requested_slots",
        ]
        for key in session_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert SESSION_JOIN in field.joins
            assert len(field.joins) == 1


class TestBuildKeypairQueryWithRealReport:
    """Integration tests for build_keypair_query with KEYPAIR_REPORT."""

    @pytest.fixture
    def adapter(self) -> ExportAdapter:
        """Create ExportAdapter instance."""
        return ExportAdapter()

    def test_basic_fields_no_joins(self, adapter: ExportAdapter) -> None:
        """Selecting only basic fields should not add JOINs."""
        query = adapter.build_keypair_query(
            report=KEYPAIR_REPORT,
            fields=["access_key", "user_id", "is_active"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        # Should be the base table, not a Join
        assert query.select_from is KeyPairRow.__table__

    def test_user_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting user fields should add 1 JOIN."""
        query = adapter.build_keypair_query(
            report=KEYPAIR_REPORT,
            fields=["access_key", "user_username"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "users" in compiled

    def test_resource_policy_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting resource policy fields should add 1 JOIN."""
        query = adapter.build_keypair_query(
            report=KEYPAIR_REPORT,
            fields=["access_key", "resource_policy_max_concurrent_sessions"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "keypair_resource_policies" in compiled

    def test_resource_group_fields_add_two_joins(self, adapter: ExportAdapter) -> None:
        """Selecting resource group fields should add 2 JOINs."""
        query = adapter.build_keypair_query(
            report=KEYPAIR_REPORT,
            fields=["access_key", "resource_group_name"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "sgroups_for_keypairs" in compiled
        assert "scaling_groups" in compiled

    def test_session_fields_add_one_join(self, adapter: ExportAdapter) -> None:
        """Selecting session fields should add 1 JOIN."""
        query = adapter.build_keypair_query(
            report=KEYPAIR_REPORT,
            fields=["access_key", "session_id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        assert "sessions" in compiled

    def test_mixed_fields_add_all_joins(self, adapter: ExportAdapter) -> None:
        """Selecting fields from all categories should add all JOINs."""
        query = adapter.build_keypair_query(
            report=KEYPAIR_REPORT,
            fields=[
                "access_key",
                "user_username",
                "resource_policy_max_concurrent_sessions",
                "resource_group_name",
                "session_id",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        compiled = str(query.select_from.compile(compile_kwargs={"literal_binds": True}))
        # All join tables should be present
        assert "users" in compiled
        assert "keypair_resource_policies" in compiled
        assert "sgroups_for_keypairs" in compiled
        assert "scaling_groups" in compiled
        assert "sessions" in compiled
