"""Unit tests verifying AND/OR/NOT logical operator behavior on AccessTokenFilter."""

from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.manager.api.gql.base import DateTimeFilter, StringFilter
from ai.backend.manager.api.gql.deployment.types.access_token import AccessTokenFilter

# Row imports to trigger mapper initialization (FK dependency order).
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow, EndpointTokenRow
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
    EndpointTokenRow,
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


class TestAccessTokenFilterAND:
    """Tests for AND logical operator on AccessTokenFilter."""

    def test_and_extends_conditions_from_sub_filter(self) -> None:
        f = AccessTokenFilter(
            AND=[AccessTokenFilter(token=StringFilter(equals="tok-abc"))],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "endpoint_tokens" in sql

    def test_and_combines_multiple_sub_filters(self) -> None:
        f = AccessTokenFilter(
            AND=[
                AccessTokenFilter(token=StringFilter(equals="tok-abc")),
                AccessTokenFilter(token=StringFilter(equals="tok-xyz")),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_and_with_empty_list_produces_no_extra_conditions(self) -> None:
        f = AccessTokenFilter(AND=[])
        conditions = f.build_conditions()
        assert conditions == []

    def test_and_combined_with_field_filter(self) -> None:
        f = AccessTokenFilter(
            token=StringFilter(equals="tok-abc"),
            AND=[AccessTokenFilter(token=StringFilter(equals="tok-xyz"))],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2


class TestAccessTokenFilterOR:
    """Tests for OR logical operator on AccessTokenFilter."""

    def test_or_wraps_sub_filters_in_single_condition(self) -> None:
        f = AccessTokenFilter(
            OR=[
                AccessTokenFilter(token=StringFilter(equals="tok-abc")),
                AccessTokenFilter(token=StringFilter(equals="tok-xyz")),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "OR" in sql

    def test_or_with_empty_list_produces_no_extra_conditions(self) -> None:
        f = AccessTokenFilter(OR=[])
        conditions = f.build_conditions()
        assert conditions == []

    def test_or_combined_with_field_filter(self) -> None:
        f = AccessTokenFilter(
            token=StringFilter(equals="tok-abc"),
            OR=[
                AccessTokenFilter(token=StringFilter(equals="tok-xyz")),
                AccessTokenFilter(token=StringFilter(equals="tok-def")),
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_or_sub_filter_with_no_conditions_skipped(self) -> None:
        f = AccessTokenFilter(OR=[AccessTokenFilter()])
        conditions = f.build_conditions()
        assert conditions == []


class TestAccessTokenFilterNOT:
    """Tests for NOT logical operator on AccessTokenFilter."""

    def test_not_wraps_sub_filter_in_negated_condition(self) -> None:
        # Use two sub-conditions so SQLAlchemy emits NOT (cond1 AND cond2) rather than !=
        f = AccessTokenFilter(
            NOT=[
                AccessTokenFilter(
                    token=StringFilter(equals="tok-revoked"),
                    created_at=DateTimeFilter(
                        before=datetime(2024, 1, 1, tzinfo=UTC),
                    ),
                )
            ],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 1
        sql = _compile(conditions[0])
        assert "NOT" in sql

    def test_not_with_empty_list_produces_no_extra_conditions(self) -> None:
        f = AccessTokenFilter(NOT=[])
        conditions = f.build_conditions()
        assert conditions == []

    def test_not_combined_with_field_filter(self) -> None:
        f = AccessTokenFilter(
            token=StringFilter(equals="tok-abc"),
            NOT=[AccessTokenFilter(token=StringFilter(equals="tok-revoked"))],
        )
        conditions = f.build_conditions()
        assert len(conditions) == 2

    def test_not_sub_filter_with_no_conditions_skipped(self) -> None:
        f = AccessTokenFilter(NOT=[AccessTokenFilter()])
        conditions = f.build_conditions()
        assert conditions == []
