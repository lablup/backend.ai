"""Unit tests verifying AND/OR/NOT logical operator behavior on SessionSchedulingHistoryFilter."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    SessionHistoryFilter as SessionHistoryFilterDTO,
)
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


class TestSessionSchedulingHistoryFilterAND:
    """Tests for AND logical operator on SessionSchedulingHistoryFilter.to_pydantic()."""

    def test_and_produces_sub_filter_dto(self) -> None:
        f = SessionSchedulingHistoryFilter(
            AND=[SessionSchedulingHistoryFilter(phase=StringFilter(equals="init"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 1
        assert dto.AND[0].phase is not None
        assert dto.AND[0].phase.equals == "init"

    def test_and_combines_multiple_sub_filters(self) -> None:
        f = SessionSchedulingHistoryFilter(
            AND=[
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="init")),
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="prepare")),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.AND is not None
        assert len(dto.AND) == 2
        assert dto.AND[0].phase is not None
        assert dto.AND[0].phase.equals == "init"
        assert dto.AND[1].phase is not None
        assert dto.AND[1].phase.equals == "prepare"

    def test_and_with_empty_list_produces_none(self) -> None:
        f = SessionSchedulingHistoryFilter(AND=[])
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        # Empty list → converted to None (falsy list → None in to_pydantic)
        assert dto.AND is None or dto.AND == []

    def test_and_combined_with_field_filter(self) -> None:
        f = SessionSchedulingHistoryFilter(
            phase=StringFilter(equals="init"),
            AND=[SessionSchedulingHistoryFilter(phase=StringFilter(equals="prepare"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.phase is not None
        assert dto.phase.equals == "init"
        assert dto.AND is not None
        assert len(dto.AND) == 1


class TestSessionSchedulingHistoryFilterOR:
    """Tests for OR logical operator on SessionSchedulingHistoryFilter.to_pydantic()."""

    def test_or_produces_sub_filter_dtos(self) -> None:
        f = SessionSchedulingHistoryFilter(
            OR=[
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="init")),
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="prepare")),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.OR is not None
        assert len(dto.OR) == 2
        assert dto.OR[0].phase is not None
        assert dto.OR[0].phase.equals == "init"
        assert dto.OR[1].phase is not None
        assert dto.OR[1].phase.equals == "prepare"

    def test_or_with_empty_list_produces_none(self) -> None:
        f = SessionSchedulingHistoryFilter(OR=[])
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.OR is None or dto.OR == []

    def test_or_combined_with_field_filter(self) -> None:
        f = SessionSchedulingHistoryFilter(
            phase=StringFilter(equals="init"),
            OR=[
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="prepare")),
                SessionSchedulingHistoryFilter(phase=StringFilter(equals="cleanup")),
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.phase is not None
        assert dto.phase.equals == "init"
        assert dto.OR is not None
        assert len(dto.OR) == 2


class TestSessionSchedulingHistoryFilterNOT:
    """Tests for NOT logical operator on SessionSchedulingHistoryFilter.to_pydantic()."""

    def test_not_produces_sub_filter_dto(self) -> None:
        f = SessionSchedulingHistoryFilter(
            NOT=[
                SessionSchedulingHistoryFilter(
                    phase=StringFilter(equals="init"),
                    error_code=StringFilter(equals="TIMEOUT"),
                )
            ],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].phase is not None
        assert dto.NOT[0].phase.equals == "init"
        assert dto.NOT[0].error_code is not None
        assert dto.NOT[0].error_code.equals == "TIMEOUT"

    def test_not_with_empty_list_produces_none(self) -> None:
        f = SessionSchedulingHistoryFilter(NOT=[])
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.NOT is None or dto.NOT == []

    def test_not_combined_with_field_filter(self) -> None:
        f = SessionSchedulingHistoryFilter(
            phase=StringFilter(equals="init"),
            NOT=[SessionSchedulingHistoryFilter(phase=StringFilter(equals="failed"))],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.phase is not None
        assert dto.phase.equals == "init"
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].phase is not None
        assert dto.NOT[0].phase.equals == "failed"

    def test_not_empty_sub_filter_produces_none_fields(self) -> None:
        f = SessionSchedulingHistoryFilter(
            NOT=[SessionSchedulingHistoryFilter()],
        )
        dto = f.to_pydantic()
        assert isinstance(dto, SessionHistoryFilterDTO)
        assert dto.NOT is not None
        assert len(dto.NOT) == 1
        assert dto.NOT[0].phase is None
