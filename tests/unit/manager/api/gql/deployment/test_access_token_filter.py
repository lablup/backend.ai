"""Unit tests verifying AND/OR/NOT logical operator behavior on AccessTokenFilter."""

from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.deployment.request import (
    AccessTokenFilter as AccessTokenFilterDTO,
)
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


class TestAccessTokenFilterAND:
    """Tests for AND logical operator on AccessTokenFilter.to_pydantic()."""

    def test_and_extends_conditions_from_sub_filter(self) -> None:
        f = AccessTokenFilter(
            AND=[AccessTokenFilter(token=StringFilter(equals="tok-abc"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 1
        assert dto.AND[0].token is not None
        assert dto.AND[0].token.equals == "tok-abc"

    def test_and_combines_multiple_sub_filters(self) -> None:
        f = AccessTokenFilter(
            AND=[
                AccessTokenFilter(token=StringFilter(equals="tok-abc")),
                AccessTokenFilter(token=StringFilter(equals="tok-xyz")),
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
            token=StringFilter(equals="tok-abc"),
            AND=[AccessTokenFilter(token=StringFilter(equals="tok-xyz"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.token is not None
        assert dto.token.equals == "tok-abc"
        assert dto.AND is not None
        assert len(dto.AND) == 1


class TestAccessTokenFilterOR:
    """Tests for OR logical operator on AccessTokenFilter.to_pydantic()."""

    def test_or_produces_sub_filter_dtos(self) -> None:
        f = AccessTokenFilter(
            OR=[
                AccessTokenFilter(token=StringFilter(equals="tok-abc")),
                AccessTokenFilter(token=StringFilter(equals="tok-xyz")),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.OR is not None
        assert len(dto.OR) == 2
        assert dto.OR[0].token is not None
        assert dto.OR[0].token.equals == "tok-abc"

    def test_or_with_empty_list_produces_none_or_empty(self) -> None:
        f = AccessTokenFilter(OR=[])
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.OR is None or dto.OR == []

    def test_or_combined_with_field_filter(self) -> None:
        f = AccessTokenFilter(
            token=StringFilter(equals="tok-abc"),
            OR=[
                AccessTokenFilter(token=StringFilter(equals="tok-xyz")),
                AccessTokenFilter(token=StringFilter(equals="tok-def")),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.token is not None
        assert dto.OR is not None
        assert len(dto.OR) == 2

    def test_or_sub_filter_with_no_field_produces_none_token(self) -> None:
        f = AccessTokenFilter(OR=[AccessTokenFilter()])
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.OR is not None
        assert dto.OR[0].token is None


class TestAccessTokenFilterNOT:
    """Tests for NOT logical operator on AccessTokenFilter.to_pydantic()."""

    def test_not_produces_sub_filter_dto(self) -> None:
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
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].token is not None
        assert dto.NOT[0].token.equals == "tok-revoked"

    def test_not_with_empty_list_produces_none_or_empty(self) -> None:
        f = AccessTokenFilter(NOT=[])
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.NOT is None or dto.NOT == []

    def test_not_combined_with_field_filter(self) -> None:
        f = AccessTokenFilter(
            token=StringFilter(equals="tok-abc"),
            NOT=[AccessTokenFilter(token=StringFilter(equals="tok-revoked"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.token is not None
        assert dto.NOT is not None
        assert len(dto.NOT) == 1

    def test_not_sub_filter_with_no_field_produces_none_token(self) -> None:
        f = AccessTokenFilter(NOT=[AccessTokenFilter()])
        dto = f.to_pydantic()
        assert isinstance(dto, AccessTokenFilterDTO)
        assert dto.NOT is not None
        assert dto.NOT[0].token is None
