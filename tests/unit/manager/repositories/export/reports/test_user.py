"""Tests for user export report definition."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.rest.export.adapter import ExportAdapter
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project.row import AssocGroupUserRow, ProjectRow
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import (
    PasswordHashAlgorithm,
    PasswordInfo,
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.base.export import ExportFieldDef, execute_streaming_export
from ai.backend.manager.repositories.export.reports.user import (
    DEFAULT_KEYPAIR_JOIN,
    PROJECT_JOIN,
    PROJECT_JOINS,
    PROJECT_MEMBERSHIP,
    PROJECT_MEMBERSHIP_JOIN,
    USER_FIELDS,
    USER_REPORT,
    USER_RESOURCE_POLICY_JOIN,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


@dataclass
class _ProjectMembers:
    project_id: uuid.UUID
    graph_member_id: uuid.UUID
    legacy_member_id: uuid.UUID


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

    def test_project_joins_order(self) -> None:
        """Project should have 2 JOINs: the graph membership, then the project."""
        assert PROJECT_JOINS == (PROJECT_MEMBERSHIP_JOIN, PROJECT_JOIN)

    def test_project_membership_join_reads_the_graph_membership(self) -> None:
        assert PROJECT_MEMBERSHIP_JOIN.table is PROJECT_MEMBERSHIP
        membership = str(PROJECT_MEMBERSHIP.compile())
        assert "entity_memberships" in membership
        assert "association_groups_users" not in membership

    def test_project_join_table(self) -> None:
        """Project JOIN should use ProjectRow table."""
        assert PROJECT_JOIN.table is ProjectRow.__table__

    def test_default_keypair_join_table(self) -> None:
        """Default keypair JOIN should use KeyPairRow table."""
        assert DEFAULT_KEYPAIR_JOIN.table is KeyPairRow.__table__


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

    def test_main_access_key_has_join(self, fields_by_key: dict[str, ExportFieldDef]) -> None:
        """main_access_key comes from the marked keypair, so it needs the keypair join."""
        field = fields_by_key["main_access_key"]
        assert field.joins is not None
        assert DEFAULT_KEYPAIR_JOIN in field.joins
        assert len(field.joins) == 1

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

    def test_main_keypair_detail_fields_have_join(
        self, fields_by_key: dict[str, ExportFieldDef]
    ) -> None:
        """Main keypair detail fields should have DEFAULT_KEYPAIR_JOIN."""
        keypair_detail_keys = [
            "main_keypair_is_active",
            "main_keypair_created_at",
            "main_keypair_last_used",
        ]
        for key in keypair_detail_keys:
            field = fields_by_key[key]
            assert field.joins is not None
            assert DEFAULT_KEYPAIR_JOIN in field.joins
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
        assert "groups" not in compiled
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
        assert "entity_memberships" in compiled
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
        # All 3 join tables should be present
        assert "user_resource_policies" in compiled
        assert "entity_memberships" in compiled
        assert "groups" in compiled
        assert "keypairs" in compiled


class TestUserExportProjectMembershipDB:
    """The project columns follow the graph membership, not the legacy association."""

    @pytest.fixture
    async def db_engine(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                ProjectRow,
                AssocGroupUserRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def members(self, db_engine: ExtendedAsyncSAEngine) -> _ProjectMembers:
        """One project: one user enrolled in the graph, one only in the legacy table."""
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"dom-{uuid.uuid4().hex[:8]}"
        project_id = uuid.uuid4()
        graph_member_id = uuid.uuid4()
        legacy_member_id = uuid.uuid4()

        async with db_engine.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
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
                max_network_count=0,
            )
            db_sess.add(user_policy)
            db_sess.add(project_policy)
            await db_sess.flush()

            for user_id in (graph_member_id, legacy_member_id):
                db_sess.add(
                    UserRow(
                        uuid=user_id,
                        username=f"user-{user_id.hex[:8]}",
                        email=f"{user_id.hex[:8]}@example.com",
                        password=PasswordInfo(
                            password="dummy",
                            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                            rounds=100_000,
                            salt_size=32,
                        ),
                        need_password_change=False,
                        status=UserStatus.ACTIVE,
                        status_info="active",
                        domain_name=domain_name,
                        role=UserRole.USER,
                        resource_policy=user_policy.name,
                        domain_id=domain_id,
                    )
                )
            db_sess.add(
                ProjectRow(
                    id=project_id,
                    name="test-project",
                    domain_name=domain_name,
                    resource_policy=project_policy.name,
                )
            )
            await db_sess.flush()

            await VirtualEntitySeeder().enroll_user_in_project(db_sess, project_id, graph_member_id)
            db_sess.add(AssocGroupUserRow(group_id=project_id, user_id=legacy_member_id))

        return _ProjectMembers(
            project_id=project_id,
            graph_member_id=graph_member_id,
            legacy_member_id=legacy_member_id,
        )

    async def test_project_id_follows_graph_membership(
        self,
        db_engine: ExtendedAsyncSAEngine,
        members: _ProjectMembers,
    ) -> None:
        query = ExportAdapter().build_user_query(
            report=USER_REPORT,
            fields=["uuid", "project_id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        project_by_user = {row[0]: row[1] for row in rows}
        assert len(rows) == 2
        assert project_by_user[members.graph_member_id] == members.project_id
        assert project_by_user[members.legacy_member_id] is None
