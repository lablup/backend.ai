"""Unit tests verifying AND/OR/NOT logical operator behavior on RoleFilter."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.rbac.request import RoleFilter as RoleFilterDTO
from ai.backend.manager.api.gql.base import StringFilter
from ai.backend.manager.api.gql.rbac.types.role import (
    RoleFilter,
    RoleSourceFilterGQL,
    RoleSourceGQL,
)

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


class TestRoleFilterNOTTypeAcceptsList:
    """Tests that RoleFilter.NOT accepts a list and converts to DTO correctly."""

    def test_not_accepts_list_of_filters(self) -> None:
        f = RoleFilter(NOT=[RoleFilter(name=StringFilter(equals="admin"))])
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].name is not None
        assert dto.NOT[0].name.equals == "admin"

    def test_not_accepts_multiple_filters_in_list(self) -> None:
        f = RoleFilter(
            NOT=[
                RoleFilter(name=StringFilter(equals="admin")),
                RoleFilter(name=StringFilter(equals="superuser")),
            ]
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.NOT is not None
        assert len(dto.NOT) == 2


class TestRoleFilterAND:
    """Tests for AND logical operator on RoleFilter.to_pydantic()."""

    def test_and_produces_sub_filter_dto(self) -> None:
        f = RoleFilter(
            AND=[RoleFilter(name=StringFilter(equals="admin"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 1
        assert dto.AND[0].name is not None
        assert dto.AND[0].name.equals == "admin"

    def test_and_combines_multiple_sub_filters(self) -> None:
        f = RoleFilter(
            AND=[
                RoleFilter(name=StringFilter(equals="admin")),
                RoleFilter(name=StringFilter(equals="editor")),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2

    def test_and_with_empty_list_produces_none(self) -> None:
        f = RoleFilter(AND=[])
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.AND is None or dto.AND == []

    def test_and_combined_with_field_filter(self) -> None:
        f = RoleFilter(
            name=StringFilter(equals="admin"),
            AND=[RoleFilter(name=StringFilter(equals="editor"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.name is not None
        assert dto.name.equals == "admin"
        assert dto.AND is not None
        assert len(dto.AND) == 1


class TestRoleFilterOR:
    """Tests for OR logical operator on RoleFilter.to_pydantic()."""

    def test_or_produces_sub_filter_dtos(self) -> None:
        f = RoleFilter(
            OR=[
                RoleFilter(name=StringFilter(equals="admin")),
                RoleFilter(name=StringFilter(equals="editor")),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.OR is not None
        assert len(dto.OR) == 2
        assert dto.OR[0].name is not None
        assert dto.OR[0].name.equals == "admin"

    def test_or_with_empty_list_produces_none(self) -> None:
        f = RoleFilter(OR=[])
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.OR is None or dto.OR == []

    def test_or_combined_with_field_filter(self) -> None:
        f = RoleFilter(
            name=StringFilter(equals="admin"),
            OR=[
                RoleFilter(name=StringFilter(equals="editor")),
                RoleFilter(name=StringFilter(equals="viewer")),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.name is not None
        assert dto.OR is not None
        assert len(dto.OR) == 2

    def test_or_empty_sub_filter_produces_none_name(self) -> None:
        f = RoleFilter(OR=[RoleFilter()])
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.OR is not None
        assert dto.OR[0].name is None


class TestRoleFilterNOT:
    """Tests for NOT logical operator on RoleFilter.to_pydantic()."""

    def test_not_produces_sub_filter_dto(self) -> None:
        f = RoleFilter(
            NOT=[
                RoleFilter(
                    name=StringFilter(equals="banned"),
                    source=RoleSourceFilterGQL(in_=[RoleSourceGQL.CUSTOM]),
                )
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].name is not None
        assert dto.NOT[0].name.equals == "banned"
        assert dto.NOT[0].source is not None

    def test_not_with_empty_list_produces_none(self) -> None:
        f = RoleFilter(NOT=[])
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.NOT is None or dto.NOT == []

    def test_not_combined_with_field_filter(self) -> None:
        f = RoleFilter(
            name=StringFilter(equals="admin"),
            NOT=[RoleFilter(name=StringFilter(equals="banned"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.name is not None
        assert dto.NOT is not None
        assert len(dto.NOT) == 1

    def test_not_empty_sub_filter_produces_none_name(self) -> None:
        f = RoleFilter(NOT=[RoleFilter()])
        dto = f.to_pydantic()
        assert isinstance(dto, RoleFilterDTO)
        assert dto.NOT is not None
        assert dto.NOT[0].name is None
