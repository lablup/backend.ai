"""Unit tests verifying AND/OR/NOT logical operator behavior on SessionSchedulingHistoryFilter."""

from __future__ import annotations

from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.gql.scheduling_history.types import SessionSchedulingHistoryFilter

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
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.scheduling_history import SessionSchedulingHistoryRow
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
    SessionSchedulingHistoryRow,
]


def _compile(condition_callable: QueryCondition) -> str:
    """Compile a QueryCondition callable to SQL string."""
    return str(condition_callable().compile(compile_kwargs={"literal_binds": True}))


class TestSessionSchedulingHistoryFilterAND:
    """Tests for AND logical operator on SessionSchedulingHistoryFilter."""

    def test_and_extends_conditions_from_sub_filter(self) -> None:
        f = SessionSchedulingHistoryFilter(
            AND=[SessionSchedulingHistoryFilter(phase=StringFilter(equals="init"))],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "session_scheduling_history" in sql

    def test_and_combines_multiple_sub_filters(self) -> None:
        f = SessionSchedulingHistoryFilter(
            AND=[
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="init")),
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="prepare")),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_and_with_empty_list_produces_no_extra_conditions(self) -> None:
        f = SessionSchedulingHistoryFilter(AND=[])
        conditions = f.build_conditions()
        assert conditions == []

    def test_and_combined_with_field_filter(self) -> None:
        f = SessionSchedulingHistoryFilter(
            phase=StringFilter(equals="init"),
            AND=[SessionSchedulingHistoryFilter(phase=StringFilter(equals="prepare"))],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2


class TestSessionSchedulingHistoryFilterOR:
    """Tests for OR logical operator on SessionSchedulingHistoryFilter."""

    def test_or_wraps_sub_filters_in_single_condition(self) -> None:
        f = SessionSchedulingHistoryFilter(
            OR=[
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="init")),
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="prepare")),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "OR" in sql

    def test_or_with_empty_list_produces_no_extra_conditions(self) -> None:
        f = SessionSchedulingHistoryFilter(OR=[])
        conditions = f.build_conditions()
        assert conditions == []

    def test_or_combined_with_field_filter(self) -> None:
        f = SessionSchedulingHistoryFilter(
            phase=StringFilter(equals="init"),
            OR=[
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="prepare")),
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="cleanup")),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_or_sub_filter_with_no_conditions_skipped(self) -> None:
        f = SessionSchedulingHistoryFilter(
            OR=[SessionSchedulingHistoryFilter()],
        )
        conditions = f.build_conditions()
        assert conditions == []


class TestSessionSchedulingHistoryFilterNOT:
    """Tests for NOT logical operator on SessionSchedulingHistoryFilter."""

    def test_not_wraps_sub_filter_in_negated_condition(self) -> None:
        # Use two sub-conditions so SQLAlchemy emits NOT (cond1 AND cond2) rather than !=
        f = SessionSchedulingHistoryFilter(
            NOT=[
                SessionSchedulingHistoryFilter(
                    phase=StringFilter(equals="init"),
                    error_code=StringFilter(equals="TIMEOUT"),
                )
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "NOT" in sql

    def test_not_with_empty_list_produces_no_extra_conditions(self) -> None:
        f = SessionSchedulingHistoryFilter(NOT=[])
        conditions = f.build_conditions()
        assert conditions == []

    def test_not_combined_with_field_filter(self) -> None:
        f = SessionSchedulingHistoryFilter(
            phase=StringFilter(equals="init"),
            NOT=[SessionSchedulingHistoryFilter(phase=StringFilter(equals="failed"))],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_not_sub_filter_with_no_conditions_skipped(self) -> None:
        f = SessionSchedulingHistoryFilter(
            NOT=[SessionSchedulingHistoryFilter()],
        )
        conditions = f.build_conditions()
        assert conditions == []
