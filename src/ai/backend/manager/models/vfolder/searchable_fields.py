"""What a vfolder search can filter and order by, and how a vfolder row becomes data."""

from __future__ import annotations

from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.entity.vfolder_mount_policy import VFolderMountPolicyID
from ai.backend.common.types import VFolderMountPolicy, VFolderUsageMode
from ai.backend.manager.data.deployment.types import ReplicaGroupLifecycle
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPolicyData,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.entity_label.searchable_fields import (
    EntityLabelCorrelation,
    EntityLabelSearchableFields,
)
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.membership import MembershipConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField
from ai.backend.manager.models.specs.search.usage import UsedByConditions
from ai.backend.manager.models.vfolder.row import VFolderRow, VFolderUserMountPolicyRow


class _VFolderOwnFields(RowDataConverter[VFolderRow, VFolderData]):
    """The vfolder's own columns."""

    id = SearchableField(VFolderRow.id, UUIDConditions(VFolderRow.id), ColumnOrder(VFolderRow.id))
    name = SearchableField(
        VFolderRow.name, StringConditions(VFolderRow.name), ColumnOrder(VFolderRow.name)
    )
    host = SearchableField(
        VFolderRow.host, StringConditions(VFolderRow.host), ColumnOrder(VFolderRow.host)
    )
    domain_name = SearchableField(
        VFolderRow.domain_name, StringConditions(VFolderRow.domain_name), ColumnOrder(VFolderRow.id)
    )
    quota_scope_id = SearchableField(
        VFolderRow.quota_scope_id,
        StringConditions(sa.type_coerce(VFolderRow.quota_scope_id, sa.String())),
        ColumnOrder(VFolderRow.quota_scope_id),
    )
    usage_mode = SearchableField(
        VFolderRow.usage_mode,
        EnumConditions(VFolderRow.usage_mode, VFolderUsageMode),
        ColumnOrder(VFolderRow.usage_mode),
    )
    default_mount_permission = SearchableField(
        VFolderRow.default_mount_permission,
        EnumConditions(VFolderRow.default_mount_permission, VFolderMountPolicy),
        ColumnOrder(VFolderRow.default_mount_permission),
    )
    created_at = SearchableField(
        VFolderRow.created_at,
        DateTimeConditions(VFolderRow.created_at),
        ColumnOrder(VFolderRow.created_at),
    )
    last_used = SearchableField(
        VFolderRow.last_used,
        DateTimeConditions(VFolderRow.last_used),
        ColumnOrder(VFolderRow.last_used),
    )
    updated_at = SearchableField(
        VFolderRow.updated_at,
        DateTimeConditions(VFolderRow.updated_at),
        ColumnOrder(VFolderRow.updated_at),
    )
    creator = SearchableField(
        VFolderRow.creator, StringConditions(VFolderRow.creator), ColumnOrder(VFolderRow.creator)
    )
    creator_id = SearchableField(
        VFolderRow.creator_id,
        UUIDConditions(VFolderRow.creator_id),
        ColumnOrder(VFolderRow.creator_id),
    )
    unmanaged_path = SearchableField(
        VFolderRow.unmanaged_path,
        StringConditions(VFolderRow.unmanaged_path),
        ColumnOrder(VFolderRow.unmanaged_path),
    )
    ownership_type = SearchableField(
        VFolderRow.ownership_type,
        EnumConditions(VFolderRow.ownership_type, VFolderOwnershipType),
        ColumnOrder(VFolderRow.ownership_type),
    )
    user = SearchableField(
        VFolderRow.user, UUIDConditions(VFolderRow.user), ColumnOrder(VFolderRow.user)
    )
    group = SearchableField(
        VFolderRow.group, UUIDConditions(VFolderRow.group), ColumnOrder(VFolderRow.group)
    )
    cloneable = SearchableField(
        VFolderRow.cloneable,
        BoolConditions(VFolderRow.cloneable),
        ColumnOrder(VFolderRow.cloneable),
    )
    status = SearchableField(
        VFolderRow.status,
        EnumConditions(VFolderRow.status, VFolderOperationStatus),
        ColumnOrder(VFolderRow.status),
    )

    @override
    def to_data(self, row: VFolderRow) -> VFolderData:
        return VFolderData(
            id=self.id.read(row),
            name=self.name.read(row),
            host=self.host.read(row),
            domain_name=self.domain_name.read(row),
            quota_scope_id=self.quota_scope_id.read(row),
            usage_mode=self.usage_mode.read(row),
            default_mount_permission=self.default_mount_permission.read(row),
            created_at=self.created_at.read(row),
            last_used=self.last_used.read(row),
            updated_at=self.updated_at.read(row),
            creator=self.creator.read(row),
            creator_id=self.creator_id.read(row),
            unmanaged_path=self.unmanaged_path.read(row),
            ownership_type=self.ownership_type.read(row),
            user=self.user.read(row),
            group=self.group.read(row),
            cloneable=self.cloneable.read(row),
            status=self.status.read(row),
        )


class _VFolderMountPolicyOwnFields(
    RowDataConverter[VFolderUserMountPolicyRow, VFolderMountPolicyData]
):
    """A mount policy row's own columns."""

    id = SearchableField(
        VFolderUserMountPolicyRow.id,
        UUIDConditions(VFolderUserMountPolicyRow.id),
        ColumnOrder(VFolderRow.status),
    )
    vfolder_id = SearchableField(
        VFolderUserMountPolicyRow.vfolder_id,
        UUIDConditions(VFolderUserMountPolicyRow.vfolder_id),
        ColumnOrder(VFolderUserMountPolicyRow.vfolder_id),
    )
    user_id = SearchableField(
        VFolderUserMountPolicyRow.user_id,
        UUIDConditions(VFolderUserMountPolicyRow.user_id),
        ColumnOrder(VFolderUserMountPolicyRow.user_id),
    )
    permission = SearchableField(
        VFolderUserMountPolicyRow.permission,
        EnumConditions(VFolderUserMountPolicyRow.permission, VFolderMountPolicy),
        ColumnOrder(VFolderUserMountPolicyRow.permission),
    )
    created_at = SearchableField(
        VFolderUserMountPolicyRow.created_at,
        DateTimeConditions(VFolderUserMountPolicyRow.created_at),
        ColumnOrder(VFolderUserMountPolicyRow.created_at),
    )
    updated_at = SearchableField(
        VFolderUserMountPolicyRow.updated_at,
        DateTimeConditions(VFolderUserMountPolicyRow.updated_at),
        ColumnOrder(VFolderUserMountPolicyRow.updated_at),
    )

    @override
    def to_data(self, row: VFolderUserMountPolicyRow) -> VFolderMountPolicyData:
        return VFolderMountPolicyData(
            id=VFolderMountPolicyID(self.id.read(row)),
            vfolder_id=self.vfolder_id.read(row),
            user_id=self.user_id.read(row),
            permission=self.permission.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class VFolderMountPolicySearchableFields:
    own = _VFolderMountPolicyOwnFields()


class _VFolderNestedFields:
    """Rows of other tables the vfolder owns: its labels and per-user mount policies."""

    labels = NestedSearchableField(
        EntityLabelSearchableFields.own,
        EntityLabelCorrelation(VFolderRow, VFolderEntityType(), VFolderRow.id),
    )
    mount_policies = NestedSearchableField(
        VFolderMountPolicySearchableFields.own,
        ToManyCorrelation(
            VFolderUserMountPolicyRow,
            VFolderRow,
            VFolderUserMountPolicyRow.vfolder_id == VFolderRow.id,
        ),
    )


class _VFolderUsage:
    """Uses between a vfolder and other entities."""

    deployments = UsedByConditions[DeploymentID](
        ToManyCorrelation(
            sa.join(
                ReplicaGroupRow,
                DeploymentRevisionRow,
                DeploymentRevisionRow.id == ReplicaGroupRow.current_revision_id,
            ),
            VFolderRow,
            sa.and_(
                ReplicaGroupRow.lifecycle.not_in(ReplicaGroupLifecycle.terminal_statuses()),
                DeploymentRevisionRow.model == VFolderRow.id,
            ),
        ),
        ReplicaGroupRow.deployment_id,
    )
    """Vfolders a live replica group's current revision names as its model."""
    model_cards = UsedByConditions[ModelCardID](
        ToManyCorrelation(ModelCardRow, VFolderRow, ModelCardRow.vfolder == VFolderRow.id),
        ModelCardRow.id,
    )
    """Vfolders a model card is built on."""


class _VFolderLinkedEntities:
    """How a vfolder connects to other entities; the other entity's permission governs."""

    membership = MembershipConditions(VFolderEntityType(), VFolderRow.id)
    usage = _VFolderUsage


class VFolderSearchableFields:
    own = _VFolderOwnFields()
    nested = _VFolderNestedFields
    linked = _VFolderLinkedEntities
