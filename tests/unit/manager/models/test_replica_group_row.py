import uuid

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)

# ORM relationship cluster registration: SQLAlchemy's global
# configure_mappers() must resolve every string relationship reachable from
# the rows this isolated test registers, so the whole domain cluster is
# imported here. _ORM_CLUSTER below keeps these imports from being pruned.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
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
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
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


def test_replica_group_lifecycle_values() -> None:
    assert ReplicaGroupLifecycle.ROLLING.value == "rolling"
    assert ReplicaGroupLifecycle.STABLE.value == "stable"
    assert ReplicaGroupLifecycle.FAILED.value == "failed"
    assert ReplicaGroupLifecycle.DRAINING.value == "draining"
    assert ReplicaGroupLifecycle.DRAINED.value == "drained"


def test_replica_group_scaling_status_values() -> None:
    assert ReplicaGroupScalingStatus.SCALING.value == "scaling"
    assert ReplicaGroupScalingStatus.STABLE.value == "stable"


def test_replica_group_status_columns_default_to_stable() -> None:
    columns = ReplicaGroupRow.__table__.columns

    lifecycle = columns["lifecycle"]
    assert lifecycle.nullable is False
    assert lifecycle.default.arg is ReplicaGroupLifecycle.STABLE
    assert lifecycle.server_default.arg == ReplicaGroupLifecycle.STABLE.value

    scaling_status = columns["scaling_status"]
    assert scaling_status.nullable is False
    assert scaling_status.default.arg is ReplicaGroupScalingStatus.STABLE
    assert scaling_status.server_default.arg == ReplicaGroupScalingStatus.STABLE.value


def _make_row() -> ReplicaGroupRow:
    return ReplicaGroupRow(
        id=ReplicaGroupID(uuid.uuid4()),
        deployment_id=DeploymentID(uuid.uuid4()),
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
        target_revision_id=DeploymentRevisionID(uuid.uuid4()),
        desired_current_replica_count=2,
        desired_target_replica_count=3,
        traffic_weight=70,
        lifecycle=ReplicaGroupLifecycle.ROLLING,
        scaling_status=ReplicaGroupScalingStatus.SCALING,
    )


def test_to_deploy_scheduling_view_carries_deploy_fields() -> None:
    row = _make_row()

    info = row.to_deploy_scheduling_view()

    assert info.group_id == row.id
    assert info.deployment_id == row.deployment_id
    assert info.current_revision_id == row.current_revision_id
    assert info.target_revision_id == row.target_revision_id
    assert info.lifecycle is ReplicaGroupLifecycle.ROLLING
    assert info.traffic_weight == 70


def test_to_scaling_scheduling_view_carries_scaling_fields() -> None:
    row = _make_row()

    info = row.to_scaling_scheduling_view()

    assert info.group_id == row.id
    assert info.deployment_id == row.deployment_id
    assert info.desired_current_replica_count == 2
    assert info.desired_target_replica_count == 3
    assert info.scaling_status is ReplicaGroupScalingStatus.SCALING
