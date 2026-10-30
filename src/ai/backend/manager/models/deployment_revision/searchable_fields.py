"""What a revision search can filter and order by, and how a revision row becomes data."""

from __future__ import annotations

from typing import override

import yarl

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.types import ClusterMode, MountPermission, ResourceSlot
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    ExecutionData,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    PresetAttributionData,
    ResourceConfigData,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetValueData
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant.searchable_fields import (
    RuntimeVariantSearchableFields,
)
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.number import FloatConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToOneCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField


class _ModelRevisionOwnFields(RowDataConverter[DeploymentRevisionRow, ModelRevisionData]):
    """The revision's own columns.

    ``model_definition``, ``resource_opts``, ``environ``, ``extra_mounts`` and
    ``preset_values`` are JSON, so none of them carries a filter or an order.
    ``startup_command``, ``bootstrap_script`` and ``callback_url`` hold values that a
    repeated partial match would recover, so both slots stay empty.
    """

    field_id = SearchableField(
        DeploymentRevisionRow.id,
        UUIDConditions(DeploymentRevisionRow.id),
        ColumnOrder(DeploymentRevisionRow.id),
    )
    deployment_id = SearchableField(
        DeploymentRevisionRow.endpoint,
        UUIDConditions(DeploymentRevisionRow.endpoint),
        ColumnOrder(DeploymentRevisionRow.endpoint),
    )
    revision_number = SearchableField(
        DeploymentRevisionRow.revision_number,
        IntConditions(DeploymentRevisionRow.revision_number),
        ColumnOrder(DeploymentRevisionRow.revision_number),
    )
    image = SearchableField(
        DeploymentRevisionRow.image,
        UUIDConditions(DeploymentRevisionRow.image),
        ColumnOrder(DeploymentRevisionRow.image),
    )
    model = SearchableField(
        DeploymentRevisionRow.model,
        UUIDConditions(DeploymentRevisionRow.model),
        ColumnOrder(DeploymentRevisionRow.model),
    )
    model_mount_destination = SearchableField(
        DeploymentRevisionRow.model_mount_destination,
        StringConditions(DeploymentRevisionRow.model_mount_destination),
        ColumnOrder(DeploymentRevisionRow.model_mount_destination),
    )
    vfolder_subpath = SearchableField(
        DeploymentRevisionRow.vfolder_subpath,
        StringConditions(DeploymentRevisionRow.vfolder_subpath),
        ColumnOrder(DeploymentRevisionRow.vfolder_subpath),
    )
    model_definition_path = SearchableField(
        DeploymentRevisionRow.model_definition_path,
        StringConditions(DeploymentRevisionRow.model_definition_path),
        ColumnOrder(DeploymentRevisionRow.model_definition_path),
    )
    model_mount_perm = SearchableField(
        DeploymentRevisionRow.model_mount_perm,
        EnumConditions(DeploymentRevisionRow.model_mount_perm, MountPermission),
        ColumnOrder(DeploymentRevisionRow.model_mount_perm),
    )
    resource_group = SearchableField(
        DeploymentRevisionRow.resource_group,
        StringConditions(DeploymentRevisionRow.resource_group),
        ColumnOrder(DeploymentRevisionRow.resource_group),
    )
    cluster_mode = SearchableField(
        DeploymentRevisionRow.cluster_mode,
        StringConditions(DeploymentRevisionRow.cluster_mode),
        ColumnOrder(DeploymentRevisionRow.cluster_mode),
    )
    cluster_size = SearchableField(
        DeploymentRevisionRow.cluster_size,
        IntConditions(DeploymentRevisionRow.cluster_size),
        ColumnOrder(DeploymentRevisionRow.cluster_size),
    )
    runtime_variant_id = SearchableField(
        DeploymentRevisionRow.runtime_variant_id,
        UUIDConditions(DeploymentRevisionRow.runtime_variant_id),
        ColumnOrder(DeploymentRevisionRow.runtime_variant_id),
    )
    termination_grace_period = SearchableField(
        DeploymentRevisionRow.termination_grace_period,
        FloatConditions(DeploymentRevisionRow.termination_grace_period),
        ColumnOrder(DeploymentRevisionRow.termination_grace_period),
    )
    revision_preset_id = SearchableField(
        DeploymentRevisionRow.revision_preset_id,
        UUIDConditions(DeploymentRevisionRow.revision_preset_id),
        ColumnOrder(DeploymentRevisionRow.revision_preset_id),
    )
    created_at = SearchableField(
        DeploymentRevisionRow.created_at,
        DateTimeConditions(DeploymentRevisionRow.created_at),
        ColumnOrder(DeploymentRevisionRow.created_at),
    )
    startup_command = SearchableField(DeploymentRevisionRow.startup_command, None, None)
    bootstrap_script = SearchableField(DeploymentRevisionRow.bootstrap_script, None, None)
    callback_url = SearchableField(DeploymentRevisionRow.callback_url, None, None)
    model_definition = SearchableField(DeploymentRevisionRow.model_definition, None, None)
    resource_opts = SearchableField(DeploymentRevisionRow.resource_opts, None, None)
    environ = SearchableField(DeploymentRevisionRow.environ, None, None)
    extra_mounts = SearchableField(DeploymentRevisionRow.extra_mounts, None, None)
    preset_values = SearchableField(DeploymentRevisionRow.preset_values, None, None)

    @override
    def to_data(self, row: DeploymentRevisionRow) -> ModelRevisionData:
        callback_url = self.callback_url.read(row)
        return ModelRevisionData(
            id=self.field_id.read(row),
            deployment_id=self.deployment_id.read(row),
            revision_number=self.revision_number.read(row),
            created_at=self.created_at.read(row),
            image_id=self.image.read(row),
            cluster_config=ClusterConfigData(
                mode=ClusterMode(self.cluster_mode.read(row)),
                size=self.cluster_size.read(row),
            ),
            resource_config=ResourceConfigData(
                resource_group_name=self.resource_group.read(row),
                # The slot quantities live in one row each; no column folds them.
                resource_slot=ResourceSlot({
                    slot.slot_name: slot.quantity for slot in row.resource_slot_rows
                }),
                resource_opts=self.resource_opts.read(row) or {},
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant_id=RuntimeVariantID(self.runtime_variant_id.read(row)),
                environ=self.environ.read(row),
                runtime_variant_preset_values=[
                    RuntimeVariantPresetValueData(preset_id=value.preset_id, value=value.value)
                    for value in (self.preset_values.read(row) or [])
                ],
            ),
            execution=ExecutionData(
                startup_command=self.startup_command.read(row),
                bootstrap_script=self.bootstrap_script.read(row),
                callback_url=yarl.URL(callback_url) if callback_url else None,
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=self.model.read(row),
                mount_destination=self.model_mount_destination.read(row),
                subpath=self.vfolder_subpath.read(row),
                definition_path=self.model_definition_path.read(row) or "",
                extra_mounts=list(self.extra_mounts.read(row)),
                model_mount_perm=self.model_mount_perm.read(row),
            ),
            revision_preset=PresetAttributionData(
                preset_id=self.revision_preset_id.read(row),
                values=[],
            ),
            model_definition=self.model_definition.read(row),
        )


class _ModelRevisionNestedFields:
    """The runtime variant the revision names.

    Reading a variant costs no permission, so the revision may order by its name; the raw
    ``runtime_variant_id`` has no meaningful order.
    """

    runtime_variant = NestedSearchableField(
        RuntimeVariantSearchableFields.own,
        ToOneCorrelation(
            RuntimeVariantRow,
            DeploymentRevisionRow,
            RuntimeVariantRow.id == DeploymentRevisionRow.runtime_variant_id,
        ),
    )


class ModelRevisionSearchableFields:
    own = _ModelRevisionOwnFields()
    nested = _ModelRevisionNestedFields
