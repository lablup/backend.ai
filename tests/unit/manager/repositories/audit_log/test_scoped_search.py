"""Integration tests for ``AuditLogRepository.scoped_search``.

Exercises the OR-union semantics of multiple :class:`SearchScope` inputs
against a real database, including mixed entity-tagged and triggered-by
scopes and combination with ``AuditLogFilter``-style narrowing conditions.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import OperationStatus

# ORM relationship cluster registration: SQLAlchemy's global
# configure_mappers() must resolve every string relationship reachable from
# the rows this isolated test registers, so the whole domain cluster is
# imported here. _ORM_CLUSTER below keeps these imports from being pruned.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.network import NetworkRow
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.rbac_models import (
    AssociationScopesEntitiesRow,
    ObjectPermissionRow,
    RoleRow,
    UserRoleRow,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset import RuntimeVariantPresetRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.vfolder import VFolderInvitationRow, VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.audit_log import (
    AuditLogCreatorSpec,
    AuditLogRepository,
    EntityAuditLogSearchScope,
    TriggeredByAuditLogSearchScope,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator, OffsetPagination
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


_ORM_CLUSTER = (
    AgentResourceRow,
    AgentRow,
    AssocGroupUserRow,
    AssociationContainerRegistriesGroupsRow,
    AssociationScopesEntitiesRow,
    ContainerRegistryRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentPolicyRow,
    DeploymentRevisionResourceSlotRow,
    DeploymentRevisionRow,
    DomainFairShareRow,
    DomainRow,
    DomainUsageBucketRow,
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
    GroupRow,
    ImageAliasRow,
    ImageRow,
    KernelRow,
    KernelUsageRecordRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    NetworkRow,
    NotificationChannelRow,
    NotificationRuleRow,
    ObjectPermissionRow,
    ProjectFairShareRow,
    ProjectResourcePolicyRow,
    ProjectUsageBucketRow,
    ReplicaGroupRow,
    ResourcePresetRow,
    ResourceSlotTypeRow,
    RoleRow,
    RoutingRow,
    RuntimeVariantPresetRow,
    RuntimeVariantRow,
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
    SessionRow,
    UserFairShareRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
    UserUsageBucketRow,
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)


@pytest.fixture
async def db_with_cleanup(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, [AuditLogRow]):
        yield database_connection


@pytest.fixture
def audit_log_repository(
    db_with_cleanup: ExtendedAsyncSAEngine,
) -> AuditLogRepository:
    return AuditLogRepository(db=db_with_cleanup)


_USER_A = str(uuid.uuid4())
_USER_B = str(uuid.uuid4())


async def _seed(
    repo: AuditLogRepository,
    *,
    entity_type: str,
    entity_id: str | None,
    triggered_by: str | None,
    operation: str = "update",
) -> uuid.UUID:
    creator = Creator(
        spec=AuditLogCreatorSpec(
            action_id=uuid.uuid4(),
            entity_type=entity_type,
            operation=operation,
            created_at=datetime.now(UTC),
            description=f"{entity_type} {operation}",
            status=OperationStatus.SUCCESS,
            entity_id=entity_id,
            request_id=None,
            triggered_by=triggered_by,
            duration=None,
        )
    )
    data = await repo.create(creator)
    return data.id


@pytest.fixture
async def seeded_audit_logs(
    audit_log_repository: AuditLogRepository,
) -> dict[str, uuid.UUID]:
    """Six rows spanning two entity targets and two actors plus one unrelated row."""
    return {
        "vfolder_vf1_by_a": await _seed(
            audit_log_repository,
            entity_type="vfolder",
            entity_id="vf-1",
            triggered_by=_USER_A,
        ),
        "vfolder_vf1_by_b": await _seed(
            audit_log_repository,
            entity_type="vfolder",
            entity_id="vf-1",
            triggered_by=_USER_B,
        ),
        "session_sess1_by_a": await _seed(
            audit_log_repository,
            entity_type="session",
            entity_id="sess-1",
            triggered_by=_USER_A,
        ),
        "session_sess2_by_b": await _seed(
            audit_log_repository,
            entity_type="session",
            entity_id="sess-2",
            triggered_by=_USER_B,
            operation="delete",
        ),
        "vfolder_vf2_by_c": await _seed(
            audit_log_repository,
            entity_type="vfolder",
            entity_id="vf-2",
            triggered_by=str(uuid.uuid4()),
        ),
        "untargeted": await _seed(
            audit_log_repository,
            entity_type="agent",
            entity_id="ag-1",
            triggered_by=None,
        ),
    }


def _empty_querier() -> BatchQuerier:
    return BatchQuerier(
        pagination=OffsetPagination(limit=50, offset=0),
        conditions=[],
        orders=[],
    )


class TestScopedSearch:
    async def test_single_entity_scope_returns_only_matching_target(
        self,
        audit_log_repository: AuditLogRepository,
        seeded_audit_logs: dict[str, uuid.UUID],
    ) -> None:
        scopes = [EntityAuditLogSearchScope(entity_type=RBACElementType.VFOLDER, entity_id="vf-1")]

        result = await audit_log_repository.scoped_search(_empty_querier(), scopes)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {
            seeded_audit_logs["vfolder_vf1_by_a"],
            seeded_audit_logs["vfolder_vf1_by_b"],
        }
        assert result.total_count == 2

    async def test_single_triggered_by_scope_returns_actor_rows(
        self,
        audit_log_repository: AuditLogRepository,
        seeded_audit_logs: dict[str, uuid.UUID],
    ) -> None:
        scopes = [TriggeredByAuditLogSearchScope(triggered_by=_USER_A)]

        result = await audit_log_repository.scoped_search(_empty_querier(), scopes)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {
            seeded_audit_logs["vfolder_vf1_by_a"],
            seeded_audit_logs["session_sess1_by_a"],
        }
        assert result.total_count == 2

    async def test_multiple_scopes_form_or_union(
        self,
        audit_log_repository: AuditLogRepository,
        seeded_audit_logs: dict[str, uuid.UUID],
    ) -> None:
        """Multiple scopes return the union — overlapping rows count once."""
        scopes = [
            EntityAuditLogSearchScope(entity_type=RBACElementType.VFOLDER, entity_id="vf-1"),
            EntityAuditLogSearchScope(entity_type=RBACElementType.SESSION, entity_id="sess-1"),
        ]

        result = await audit_log_repository.scoped_search(_empty_querier(), scopes)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {
            seeded_audit_logs["vfolder_vf1_by_a"],
            seeded_audit_logs["vfolder_vf1_by_b"],
            seeded_audit_logs["session_sess1_by_a"],
        }
        assert result.total_count == 3

    async def test_mixed_entity_and_triggered_by_scopes(
        self,
        audit_log_repository: AuditLogRepository,
        seeded_audit_logs: dict[str, uuid.UUID],
    ) -> None:
        """Entity-tagged and triggered-by scopes combine as a single OR group."""
        scopes = [
            EntityAuditLogSearchScope(entity_type=RBACElementType.VFOLDER, entity_id="vf-1"),
            TriggeredByAuditLogSearchScope(triggered_by=_USER_B),
        ]

        result = await audit_log_repository.scoped_search(_empty_querier(), scopes)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {
            seeded_audit_logs["vfolder_vf1_by_a"],
            seeded_audit_logs["vfolder_vf1_by_b"],
            seeded_audit_logs["session_sess2_by_b"],
        }
        assert result.total_count == 3

    async def test_querier_conditions_narrow_within_scope_union(
        self,
        audit_log_repository: AuditLogRepository,
        seeded_audit_logs: dict[str, uuid.UUID],
    ) -> None:
        """Additional ``querier.conditions`` AND-narrow the OR'd union."""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=50, offset=0),
            conditions=[lambda: AuditLogRow.operation == "delete"],
            orders=[],
        )
        scopes = [
            EntityAuditLogSearchScope(entity_type=RBACElementType.VFOLDER, entity_id="vf-1"),
            EntityAuditLogSearchScope(entity_type=RBACElementType.SESSION, entity_id="sess-2"),
        ]

        result = await audit_log_repository.scoped_search(querier, scopes)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {seeded_audit_logs["session_sess2_by_b"]}
        assert result.total_count == 1
