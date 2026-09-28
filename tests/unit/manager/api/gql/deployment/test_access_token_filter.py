"""Unit tests verifying AND/OR/NOT logical operator behavior on AccessTokenFilter."""

from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.deployment.request import (
    AccessTokenFilter as AccessTokenFilterDTO,
)
from ai.backend.manager.api.gql.base import DateTimeFilter
from ai.backend.manager.api.gql.deployment.types.access_token import AccessTokenFilter

# Row imports to trigger mapper initialization (FK dependency order).
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow, EndpointTokenRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.vfolder.row import VFolderRow

# Reference Row models to prevent unused-import removal.
_MAPPER_ROWS = [
    DomainRow,
    ResourceGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    EndpointTokenRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    ReplicaGroupRow,
    RoutingRow,
    ResourcePresetRow,
]

_T1 = datetime(2026, 1, 1, tzinfo=UTC)
_T2 = datetime(2026, 2, 1, tzinfo=UTC)
_T3 = datetime(2026, 3, 1, tzinfo=UTC)


class TestAccessTokenFilterAND:
    """Tests for AND logical operator on AccessTokenFilter.to_pydantic()."""

    def test_and_extends_conditions_from_sub_filter(self) -> None:
        f = AccessTokenFilter(
            AND=[AccessTokenFilter(expires_at=DateTimeFilter(equals=_T1))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 1
        assert dto.AND[0].expires_at is not None
        assert dto.AND[0].expires_at.equals == _T1

    def test_and_combines_multiple_sub_filters(self) -> None:
        f = AccessTokenFilter(
            AND=[
                AccessTokenFilter(expires_at=DateTimeFilter(equals=_T1)),
                AccessTokenFilter(expires_at=DateTimeFilter(equals=_T2)),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2

    def test_and_with_empty_list_produces_none_or_empty(self) -> None:
        f = AccessTokenFilter(AND=[])
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.AND is None or dto.AND == []

    def test_and_combined_with_field_filter(self) -> None:
        f = AccessTokenFilter(
            expires_at=DateTimeFilter(equals=_T1),
            AND=[AccessTokenFilter(expires_at=DateTimeFilter(equals=_T2))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.expires_at is not None
        assert dto.expires_at.equals == _T1
        assert dto.AND is not None
        assert len(dto.AND) == 1


class TestAccessTokenFilterOR:
    """Tests for OR logical operator on AccessTokenFilter.to_pydantic()."""

    def test_or_produces_sub_filter_dtos(self) -> None:
        f = AccessTokenFilter(
            OR=[
                AccessTokenFilter(expires_at=DateTimeFilter(equals=_T1)),
                AccessTokenFilter(expires_at=DateTimeFilter(equals=_T2)),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.OR is not None
        assert len(dto.OR) == 2
        assert dto.OR[0].expires_at is not None
        assert dto.OR[0].expires_at.equals == _T1

    def test_or_with_empty_list_produces_none_or_empty(self) -> None:
        f = AccessTokenFilter(OR=[])
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.OR is None or dto.OR == []

    def test_or_combined_with_field_filter(self) -> None:
        f = AccessTokenFilter(
            expires_at=DateTimeFilter(equals=_T1),
            OR=[
                AccessTokenFilter(expires_at=DateTimeFilter(equals=_T2)),
                AccessTokenFilter(expires_at=DateTimeFilter(equals=_T3)),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.expires_at is not None
        assert dto.OR is not None
        assert len(dto.OR) == 2

    def test_or_sub_filter_with_no_field_produces_none_token(self) -> None:
        f = AccessTokenFilter(OR=[AccessTokenFilter()])
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.OR is not None
        assert dto.OR[0].expires_at is None


class TestAccessTokenFilterNOT:
    """Tests for NOT logical operator on AccessTokenFilter.to_pydantic()."""

    def test_not_produces_sub_filter_dto(self) -> None:
        f = AccessTokenFilter(
            NOT=[
                AccessTokenFilter(
                    expires_at=DateTimeFilter(equals=_T3),
                    created_at=DateTimeFilter(
                        before=datetime(2024, 1, 1, tzinfo=UTC),
                    ),
                )
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].expires_at is not None
        assert dto.NOT[0].expires_at.equals == _T3

    def test_not_with_empty_list_produces_none_or_empty(self) -> None:
        f = AccessTokenFilter(NOT=[])
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.NOT is None or dto.NOT == []

    def test_not_combined_with_field_filter(self) -> None:
        f = AccessTokenFilter(
            expires_at=DateTimeFilter(equals=_T1),
            NOT=[AccessTokenFilter(expires_at=DateTimeFilter(equals=_T3))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.expires_at is not None
        assert dto.NOT is not None
        assert len(dto.NOT) == 1

    def test_not_sub_filter_with_no_field_produces_none_token(self) -> None:
        f = AccessTokenFilter(NOT=[AccessTokenFilter()])
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.NOT is not None
        assert dto.NOT[0].expires_at is None
