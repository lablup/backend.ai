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
from ai.backend.manager.api.rest.export.adapter import ExportAdapter
from ai.backend.manager.models.agent import AgentRow
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
    execute_streaming_export,
)
from ai.backend.manager.repositories.export.reports.project import (
    PROJECT_FIELDS,
    PROJECT_REPORT,
    RESOURCE_POLICY_JOIN,
    _serialize_json,
)
from ai.backend.testutils.db import with_tables

# Reference Row models to prevent unused-import removal (mapper initialization).
_MAPPER_ROWS = [AgentRow]

_RESOURCE_POLICY_FIELD_KEYS = {
    "resource_policy_name",
    "resource_policy_max_vfolder_count",
    "resource_policy_max_quota_scope_size",
    "resource_policy_max_network_count",
    "resource_policy_created_at",
}
_SCALING_GROUP_FIELD_KEYS = {
    "scaling_group_name",
    "scaling_group_description",
    "scaling_group_is_active",
    "scaling_group_is_public",
    "scaling_group_driver",
    "scaling_group_scheduler",
    "scaling_group_created_at",
}
_CONTAINER_REGISTRY_FIELD_KEYS = {
    "container_registry_id",
    "container_registry_url",
    "container_registry_name",
    "container_registry_type",
    "container_registry_project",
    "container_registry_is_global",
}

_DOMAIN_NAME = "test-domain"
_POLICY_NAME = "test-policy"
_SG_ALPHA = "sg-alpha"
_SG_BETA = "sg-beta"


@dataclass(frozen=True)
class _ProjectScalingGroupScenario:
    """Three projects bound to zero, one and two scaling groups."""

    project_without_sg: uuid.UUID
    project_with_one_sg: uuid.UUID
    project_with_two_sgs: uuid.UUID


@dataclass(frozen=True)
class _ProjectRegistryScenario:
    """Two projects sharing a global registry, one of them owning a scoped registry too."""

    associated_project_id: uuid.UUID
    unassociated_project_id: uuid.UUID
    global_registry_id: uuid.UUID
    scoped_registry_id: uuid.UUID


@dataclass(frozen=True)
class _AggregatedCellCase:
    """Expected content of a 1:N field's single cell for one project."""

    project_name: str
    expected_cell: str | None


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
        """Should have 28 fields total."""
        assert len(PROJECT_REPORT.fields) == 28


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

    def test_container_registry_field_exists(self, field_keys: set[str]) -> None:
        """container_registry (image commit registry) field should exist."""
        assert "container_registry" in field_keys

    def test_resource_policy_fields_exist(self, field_keys: set[str]) -> None:
        """Resource policy fields should exist."""
        assert _RESOURCE_POLICY_FIELD_KEYS.issubset(field_keys)

    def test_scaling_group_fields_exist(self, field_keys: set[str]) -> None:
        """Scaling group fields should exist."""
        assert _SCALING_GROUP_FIELD_KEYS.issubset(field_keys)

    def test_container_registry_fields_exist(self, field_keys: set[str]) -> None:
        """Container registry fields should exist."""
        assert _CONTAINER_REGISTRY_FIELD_KEYS.issubset(field_keys)


class TestFieldJoinAssignments:
    """Only N:1 relations may be reached through a join.

    A 1:N relation joined into the main query multiplies the exported rows, so
    those fields must carry a correlated aggregate instead.
    """

    @pytest.fixture
    def fields_by_key(self) -> dict[str, ExportFieldDef]:
        """Map of field key to field definition."""
        return {f.key: f for f in PROJECT_FIELDS}

    def test_resource_policy_join_table(self) -> None:
        """Resource policy JOIN should use ProjectResourcePolicyRow table."""
        assert RESOURCE_POLICY_JOIN.table is ProjectResourcePolicyRow.__table__

    def test_only_resource_policy_fields_declare_joins(self) -> None:
        """The N:1 resource policy is the only relation declared as a join."""
        keys_with_joins = {f.key for f in PROJECT_FIELDS if f.joins}
        assert keys_with_joins == _RESOURCE_POLICY_FIELD_KEYS

    @pytest.mark.parametrize("key", sorted(_RESOURCE_POLICY_FIELD_KEYS))
    def test_resource_policy_fields_have_single_join(
        self, fields_by_key: dict[str, ExportFieldDef], key: str
    ) -> None:
        """Resource policy fields require exactly RESOURCE_POLICY_JOIN."""
        field = fields_by_key[key]
        assert field.joins is not None
        assert RESOURCE_POLICY_JOIN in field.joins
        assert len(field.joins) == 1

    @pytest.mark.parametrize(
        "key", sorted(_SCALING_GROUP_FIELD_KEYS | _CONTAINER_REGISTRY_FIELD_KEYS)
    )
    def test_one_to_many_fields_aggregate_instead_of_joining(
        self, fields_by_key: dict[str, ExportFieldDef], key: str
    ) -> None:
        """1:N fields declare no join and select an aggregate expression."""
        field = fields_by_key[key]
        assert field.joins is None
        compiled = str(sa.select(field.column).compile(compile_kwargs={"literal_binds": True}))
        assert "string_agg" in compiled


class TestBuildProjectQueryShape:
    """Tests for the FROM clause build_project_query produces."""

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
        assert compiled.count("LEFT OUTER JOIN") == 1
        assert "project_resource_policies" in compiled

    @pytest.mark.parametrize(
        "fields",
        [
            ["id", "scaling_group_name"],
            ["id", "container_registry_url"],
            ["id", "scaling_group_name", "container_registry_url"],
            [
                "id",
                "scaling_group_name",
                "scaling_group_description",
                "container_registry_id",
                "container_registry_url",
                "container_registry_name",
            ],
        ],
        ids=lambda fields: "+".join(fields[1:]),
    )
    def test_one_to_many_fields_do_not_join(
        self, adapter: ExportAdapter, fields: list[str]
    ) -> None:
        """No combination of 1:N fields may widen the FROM clause."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=fields,
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        assert query.select_from is GroupRow.__table__

    def test_reported_field_combination_joins_only_resource_policy(
        self, adapter: ExportAdapter
    ) -> None:
        """The reported field list must join the resource policy table and nothing else."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=[
                "name",
                "domain_name",
                "description",
                "created_at",
                "total_resource_slots",
                "resource_policy_name",
                "allowed_vfolder_hosts",
                "scaling_group_name",
                "container_registry",
                "id",
            ],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        columns = [f.column for f in query.fields]
        compiled = str(
            sa.select(*columns)
            .select_from(query.select_from)
            .compile(compile_kwargs={"literal_binds": True})
        )
        assert compiled.count("LEFT OUTER JOIN") == 1
        assert "project_resource_policies" in compiled

    def test_all_fields_selected_when_none_specified(self, adapter: ExportAdapter) -> None:
        """None for fields should select all 28 fields."""
        query = adapter.build_project_query(
            report=PROJECT_REPORT,
            fields=None,
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        assert len(query.fields) == 28


class TestProjectExportRowMultiplicity:
    """DB-level tests: the export must stay at one row per project."""

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
    async def scaling_group_scenario(
        self,
        db_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[_ProjectScalingGroupScenario, None]:
        """Three projects bound to zero, one and two scaling groups."""
        project_without_sg = uuid.uuid4()
        project_with_one_sg = uuid.uuid4()
        project_with_two_sgs = uuid.uuid4()

        async with db_engine.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=_DOMAIN_NAME,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=_POLICY_NAME,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=project_without_sg,
                    name="project-no-sg",
                    domain_name=_DOMAIN_NAME,
                    resource_policy=_POLICY_NAME,
                )
            )
            db_sess.add(
                GroupRow(
                    id=project_with_one_sg,
                    name="project-one-sg",
                    domain_name=_DOMAIN_NAME,
                    resource_policy=_POLICY_NAME,
                )
            )
            db_sess.add(
                GroupRow(
                    id=project_with_two_sgs,
                    name="project-two-sgs",
                    domain_name=_DOMAIN_NAME,
                    resource_policy=_POLICY_NAME,
                )
            )
            for sg_name in (_SG_ALPHA, _SG_BETA):
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

            db_sess.add(
                ScalingGroupForProjectRow(scaling_group=_SG_ALPHA, group=project_with_one_sg)
            )
            db_sess.add(
                ScalingGroupForProjectRow(scaling_group=_SG_ALPHA, group=project_with_two_sgs)
            )
            db_sess.add(
                ScalingGroupForProjectRow(scaling_group=_SG_BETA, group=project_with_two_sgs)
            )
            await db_sess.commit()

        yield _ProjectScalingGroupScenario(
            project_without_sg=project_without_sg,
            project_with_one_sg=project_with_one_sg,
            project_with_two_sgs=project_with_two_sgs,
        )

    @pytest.fixture
    async def registry_scenario(
        self,
        db_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[_ProjectRegistryScenario, None]:
        """Two projects sharing a global registry, one also owning a scoped registry."""
        associated_project_id = uuid.uuid4()
        unassociated_project_id = uuid.uuid4()
        global_registry_id = uuid.uuid4()
        scoped_registry_id = uuid.uuid4()

        async with db_engine.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=_DOMAIN_NAME,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=_POLICY_NAME,
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=10,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=associated_project_id,
                    name="project-associated",
                    domain_name=_DOMAIN_NAME,
                    resource_policy=_POLICY_NAME,
                )
            )
            db_sess.add(
                GroupRow(
                    id=unassociated_project_id,
                    name="project-unassociated",
                    domain_name=_DOMAIN_NAME,
                    resource_policy=_POLICY_NAME,
                )
            )
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
                    group_id=associated_project_id,
                )
            )
            await db_sess.commit()

        yield _ProjectRegistryScenario(
            associated_project_id=associated_project_id,
            unassociated_project_id=unassociated_project_id,
            global_registry_id=global_registry_id,
            scoped_registry_id=scoped_registry_id,
        )

    async def test_scaling_group_field_keeps_one_row_per_project(
        self,
        db_engine: ExtendedAsyncSAEngine,
        scaling_group_scenario: _ProjectScalingGroupScenario,
    ) -> None:
        """Selecting scaling_group_name must not multiply rows for multi-group projects."""
        query = ExportAdapter().build_project_query(
            report=PROJECT_REPORT,
            fields=["name", "scaling_group_name", "id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        exported_ids = {str(row[2]) for row in rows}
        assert len(rows) == 3
        assert exported_ids == {
            str(scaling_group_scenario.project_without_sg),
            str(scaling_group_scenario.project_with_one_sg),
            str(scaling_group_scenario.project_with_two_sgs),
        }

    @pytest.mark.parametrize(
        "case",
        [
            _AggregatedCellCase(project_name="project-no-sg", expected_cell=None),
            _AggregatedCellCase(project_name="project-one-sg", expected_cell=_SG_ALPHA),
            _AggregatedCellCase(
                project_name="project-two-sgs", expected_cell=f"{_SG_ALPHA}, {_SG_BETA}"
            ),
        ],
        ids=lambda case: case.project_name,
    )
    async def test_scaling_group_names_are_aggregated_into_one_cell(
        self,
        db_engine: ExtendedAsyncSAEngine,
        scaling_group_scenario: _ProjectScalingGroupScenario,
        case: _AggregatedCellCase,
    ) -> None:
        """Every allowed scaling group appears in the project's single cell, sorted."""
        query = ExportAdapter().build_project_query(
            report=PROJECT_REPORT,
            fields=["name", "scaling_group_name", "id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        cells = {row[0]: row[1] for row in rows}
        assert cells[case.project_name] == case.expected_cell

    async def test_container_registry_field_keeps_one_row_per_project(
        self,
        db_engine: ExtendedAsyncSAEngine,
        registry_scenario: _ProjectRegistryScenario,
    ) -> None:
        """A global registry visible to every project must not multiply rows."""
        query = ExportAdapter().build_project_query(
            report=PROJECT_REPORT,
            fields=["name", "container_registry_name", "id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        exported_ids = {str(row[2]) for row in rows}
        assert len(rows) == 2
        assert exported_ids == {
            str(registry_scenario.associated_project_id),
            str(registry_scenario.unassociated_project_id),
        }

    @pytest.mark.parametrize(
        "case",
        [
            _AggregatedCellCase(
                project_name="project-associated",
                expected_cell="global-registry, scoped-registry",
            ),
            _AggregatedCellCase(
                project_name="project-unassociated",
                expected_cell="global-registry",
            ),
        ],
        ids=lambda case: case.project_name,
    )
    async def test_available_registries_are_aggregated_into_one_cell(
        self,
        db_engine: ExtendedAsyncSAEngine,
        registry_scenario: _ProjectRegistryScenario,
        case: _AggregatedCellCase,
    ) -> None:
        """Global registries reach every project; scoped ones only their own (BA-4708)."""
        query = ExportAdapter().build_project_query(
            report=PROJECT_REPORT,
            fields=["name", "container_registry_name", "id"],
            filter=None,
            order=None,
            max_rows=1000,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        cells = {row[0]: row[1] for row in rows}
        assert cells[case.project_name] == case.expected_cell

    async def test_reported_field_combination_keeps_one_row_per_project(
        self,
        db_engine: ExtendedAsyncSAEngine,
        scaling_group_scenario: _ProjectScalingGroupScenario,
    ) -> None:
        """The reported field list must export exactly one row per project."""
        query = ExportAdapter().build_project_query(
            report=PROJECT_REPORT,
            fields=[
                "name",
                "domain_name",
                "description",
                "created_at",
                "total_resource_slots",
                "resource_policy_name",
                "allowed_vfolder_hosts",
                "scaling_group_name",
                "container_registry",
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

        assert len(rows) == 3
        assert {str(row[9]) for row in rows} == {
            str(scaling_group_scenario.project_without_sg),
            str(scaling_group_scenario.project_with_one_sg),
            str(scaling_group_scenario.project_with_two_sgs),
        }

    async def test_max_rows_limits_projects_not_joined_rows(
        self,
        db_engine: ExtendedAsyncSAEngine,
        scaling_group_scenario: _ProjectScalingGroupScenario,
    ) -> None:
        """max_rows caps the number of exported projects."""
        query = ExportAdapter().build_project_query(
            report=PROJECT_REPORT,
            fields=["name", "scaling_group_name", "id"],
            filter=None,
            order=None,
            max_rows=2,
            statement_timeout_sec=60,
        )

        rows: list[Any] = []
        async for partition in execute_streaming_export(db_engine, query):
            rows.extend(partition)

        assert len(rows) == 2
        assert len({str(row[2]) for row in rows}) == 2


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
