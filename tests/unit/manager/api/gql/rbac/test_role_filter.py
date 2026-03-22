"""Unit tests verifying AND/OR/NOT logical operator behavior on RoleFilter."""

from __future__ import annotations

from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.gql.rbac.types.role import RoleFilter, RoleSourceGQL

# Row imports to trigger mapper initialization (FK dependency order).
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
from ai.backend.manager.models.rbac_models.role import RoleRow
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
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import QueryCondition

# Reference Row models to prevent unused-import removal.
_MAPPER_ROWS = [
    DomainRow,
    ScalingGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRoleRow,
    RoleRow,
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


def _compile(condition_callable: QueryCondition) -> str:
    """Compile a QueryCondition callable to SQL string."""
    return str(condition_callable().compile(compile_kwargs={"literal_binds": True}))


class TestRoleFilterNOTTypeAcceptsList:
    """Tests that RoleFilter.NOT accepts a list (bug fix: was singular)."""

    def test_not_accepts_list_of_filters(self) -> None:
        f = RoleFilter(NOT=[RoleFilter(name=StringFilter(equals="admin"))])
        conditions = f.build_conditions()
        assert len(conditions) == 1

    def test_not_accepts_multiple_filters_in_list(self) -> None:
        f = RoleFilter(
            NOT=[
                RoleFilter(name=StringFilter(equals="admin")),
                RoleFilter(name=StringFilter(equals="superuser")),
            ]
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "NOT" in sql


class TestRoleFilterAND:
    """Tests for AND logical operator on RoleFilter."""

    def test_and_extends_conditions_from_sub_filter(self) -> None:
        f = RoleFilter(
            AND=[RoleFilter(name=StringFilter(equals="admin"))],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "roles" in sql

    def test_and_combines_multiple_sub_filters(self) -> None:
        f = RoleFilter(
            AND=[
                RoleFilter(name=StringFilter(equals="admin")),
                RoleFilter(name=StringFilter(equals="editor")),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_and_with_empty_list_produces_no_extra_conditions(self) -> None:
        f = RoleFilter(AND=[])
        conditions = f.build_conditions()
        assert conditions == []

    def test_and_combined_with_field_filter(self) -> None:
        f = RoleFilter(
            name=StringFilter(equals="admin"),
            AND=[RoleFilter(name=StringFilter(equals="editor"))],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2


class TestRoleFilterOR:
    """Tests for OR logical operator on RoleFilter."""

    def test_or_wraps_sub_filters_in_single_condition(self) -> None:
        f = RoleFilter(
            OR=[
                RoleFilter(name=StringFilter(equals="admin")),
                RoleFilter(name=StringFilter(equals="editor")),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "OR" in sql

    def test_or_with_empty_list_produces_no_extra_conditions(self) -> None:
        f = RoleFilter(OR=[])
        conditions = f.build_conditions()
        assert conditions == []

    def test_or_combined_with_field_filter(self) -> None:
        f = RoleFilter(
            name=StringFilter(equals="admin"),
            OR=[
                RoleFilter(name=StringFilter(equals="editor")),
                RoleFilter(name=StringFilter(equals="viewer")),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_or_sub_filter_with_no_conditions_skipped(self) -> None:
        f = RoleFilter(OR=[RoleFilter()])
        conditions = f.build_conditions()
        assert conditions == []


class TestRoleFilterNOT:
    """Tests for NOT logical operator on RoleFilter."""

    def test_not_wraps_sub_filter_in_negated_condition(self) -> None:
        # Use two sub-conditions so SQLAlchemy emits NOT (cond1 AND cond2) rather than !=
        f = RoleFilter(
            NOT=[
                RoleFilter(
                    name=StringFilter(equals="banned"),
                    source=[RoleSourceGQL.CUSTOM],
                )
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "NOT" in sql

    def test_not_with_empty_list_produces_no_extra_conditions(self) -> None:
        f = RoleFilter(NOT=[])
        conditions = f.build_conditions()
        assert conditions == []

    def test_not_combined_with_field_filter(self) -> None:
        f = RoleFilter(
            name=StringFilter(equals="admin"),
            NOT=[RoleFilter(name=StringFilter(equals="banned"))],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_not_sub_filter_with_no_conditions_skipped(self) -> None:
        f = RoleFilter(NOT=[RoleFilter()])
        conditions = f.build_conditions()
        assert conditions == []
