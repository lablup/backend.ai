"""Unit tests for ResourceGroup GraphQL filter and order-by types."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.resource_group.request import (
    ResourceGroupFilter as ResourceGroupFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    ResourceGroupOrder as ResourceGroupOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    ResourceGroupOrderDirection as ResourceGroupOrderDirectionEnum,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    ResourceGroupOrderField as ResourceGroupOrderFieldEnum,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.resource_group.types import (
    ResourceGroupFilterGQL,
    ResourceGroupOrderByGQL,
    ResourceGroupOrderFieldGQL,
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
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    RoutingRow,
    ResourcePresetRow,
]


class TestResourceGroupFilter:
    """Tests for ResourceGroupFilterGQL.to_pydantic() method."""

    def test_name_filter(self) -> None:
        f = ResourceGroupFilterGQL(name=StringFilter(contains="gpu"))
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.name is not None
        assert dto.name.contains == "gpu"

    def test_description_filter(self) -> None:
        f = ResourceGroupFilterGQL(description=StringFilter(contains="production"))
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.description is not None
        assert dto.description.contains == "production"

    def test_is_active_true_filter(self) -> None:
        f = ResourceGroupFilterGQL(is_active=True)
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.is_active is True

    def test_is_active_false_filter(self) -> None:
        f = ResourceGroupFilterGQL(is_active=False)
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.is_active is False

    def test_is_public_filter(self) -> None:
        f = ResourceGroupFilterGQL(is_public=True)
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.is_public is True

    def test_combined_filters(self) -> None:
        f = ResourceGroupFilterGQL(
            name=StringFilter(contains="gpu"),
            is_active=True,
            is_public=False,
        )
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.name is not None
        assert dto.name.contains == "gpu"
        assert dto.is_active is True
        assert dto.is_public is False

    def test_empty_filter_returns_dto_with_none_fields(self) -> None:
        f = ResourceGroupFilterGQL()
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.name is None
        assert dto.description is None
        assert dto.is_active is None
        assert dto.is_public is None

    def test_description_with_name_combined(self) -> None:
        f = ResourceGroupFilterGQL(
            name=StringFilter(equals="default"),
            description=StringFilter(contains="test"),
        )
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.name is not None
        assert dto.name.equals == "default"
        assert dto.description is not None
        assert dto.description.contains == "test"

    def test_or_logical_operator(self) -> None:
        f = ResourceGroupFilterGQL(
            OR=[
                ResourceGroupFilterGQL(is_active=True),
                ResourceGroupFilterGQL(is_public=True),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.OR is not None
        assert len(dto.OR) == 2
        assert dto.OR[0].is_active is True
        assert dto.OR[1].is_public is True

    def test_not_logical_operator(self) -> None:
        f = ResourceGroupFilterGQL(
            NOT=[ResourceGroupFilterGQL(is_active=False)],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, ResourceGroupFilterDTO)
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].is_active is False


class TestResourceGroupOrderBy:
    """Tests for ResourceGroupOrderByGQL.to_pydantic() method."""

    def test_name_ascending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.NAME,
            direction=OrderDirection.ASC,
        )
        dto = order.to_pydantic()
        assert isinstance(dto, ResourceGroupOrderDTO)
        assert dto.field == ResourceGroupOrderFieldEnum.NAME
        assert dto.direction == ResourceGroupOrderDirectionEnum.ASC

    def test_name_descending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.NAME,
            direction=OrderDirection.DESC,
        )
        dto = order.to_pydantic()
        assert isinstance(dto, ResourceGroupOrderDTO)
        assert dto.field == ResourceGroupOrderFieldEnum.NAME
        assert dto.direction == ResourceGroupOrderDirectionEnum.DESC

    def test_created_at_ascending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.CREATED_AT,
            direction=OrderDirection.ASC,
        )
        dto = order.to_pydantic()
        assert isinstance(dto, ResourceGroupOrderDTO)
        assert dto.field == ResourceGroupOrderFieldEnum.CREATED_AT
        assert dto.direction == ResourceGroupOrderDirectionEnum.ASC

    def test_created_at_descending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.CREATED_AT,
            direction=OrderDirection.DESC,
        )
        dto = order.to_pydantic()
        assert isinstance(dto, ResourceGroupOrderDTO)
        assert dto.field == ResourceGroupOrderFieldEnum.CREATED_AT
        assert dto.direction == ResourceGroupOrderDirectionEnum.DESC

    def test_is_active_ascending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.IS_ACTIVE,
            direction=OrderDirection.ASC,
        )
        dto = order.to_pydantic()
        assert isinstance(dto, ResourceGroupOrderDTO)
        assert dto.field == ResourceGroupOrderFieldEnum.IS_ACTIVE
        assert dto.direction == ResourceGroupOrderDirectionEnum.ASC

    def test_is_active_descending(self) -> None:
        order = ResourceGroupOrderByGQL(
            field=ResourceGroupOrderFieldGQL.IS_ACTIVE,
            direction=OrderDirection.DESC,
        )
        dto = order.to_pydantic()
        assert isinstance(dto, ResourceGroupOrderDTO)
        assert dto.field == ResourceGroupOrderFieldEnum.IS_ACTIVE
        assert dto.direction == ResourceGroupOrderDirectionEnum.DESC
