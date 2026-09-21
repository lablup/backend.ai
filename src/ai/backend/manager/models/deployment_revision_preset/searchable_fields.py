"""What a deployment preset search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    EnvironEntryData,
    ResourceOptsEntryData,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetValueData
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    PresetResourceSlotRow,
)
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.specs.search.usage import UsedByConditions


class _DeploymentPresetOwnFields(
    RowDataConverter[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """The preset's own columns.

    ``description`` is ``sa.Text`` with no index serving partial matches;
    ``model_definition``, ``resource_opts``, ``environ``, ``preset_values`` and
    ``deployment_strategy_spec`` are JSON. ``startup_command`` and ``bootstrap_script``
    are user-written scripts, so repeating a filter would recover them.
    """

    id = SearchableField(
        DeploymentRevisionPresetRow.id,
        UUIDConditions(DeploymentRevisionPresetRow.id),
        ColumnOrder(DeploymentRevisionPresetRow.id),
    )
    runtime_variant_id = SearchableField(
        DeploymentRevisionPresetRow.runtime_variant,
        UUIDConditions(DeploymentRevisionPresetRow.runtime_variant),
        ColumnOrder(DeploymentRevisionPresetRow.runtime_variant),
    )
    name = SearchableField(
        DeploymentRevisionPresetRow.name,
        StringConditions(DeploymentRevisionPresetRow.name),
        ColumnOrder(DeploymentRevisionPresetRow.name),
    )
    description = SearchableField(DeploymentRevisionPresetRow.description, None, None)
    rank = SearchableField(
        DeploymentRevisionPresetRow.rank,
        IntConditions(DeploymentRevisionPresetRow.rank),
        ColumnOrder(DeploymentRevisionPresetRow.rank),
    )
    image_id = SearchableField(
        DeploymentRevisionPresetRow.image_id,
        UUIDConditions(DeploymentRevisionPresetRow.image_id),
        ColumnOrder(DeploymentRevisionPresetRow.image_id),
    )
    model_definition = SearchableField(DeploymentRevisionPresetRow.model_definition, None, None)
    resource_opts = SearchableField(DeploymentRevisionPresetRow.resource_opts, None, None)
    cluster_mode = SearchableField(
        DeploymentRevisionPresetRow.cluster_mode,
        StringConditions(DeploymentRevisionPresetRow.cluster_mode),
        ColumnOrder(DeploymentRevisionPresetRow.cluster_mode),
    )
    cluster_size = SearchableField(
        DeploymentRevisionPresetRow.cluster_size,
        IntConditions(DeploymentRevisionPresetRow.cluster_size),
        ColumnOrder(DeploymentRevisionPresetRow.cluster_size),
    )
    startup_command = SearchableField(DeploymentRevisionPresetRow.startup_command, None, None)
    bootstrap_script = SearchableField(DeploymentRevisionPresetRow.bootstrap_script, None, None)
    environ = SearchableField(DeploymentRevisionPresetRow.environ, None, None)
    runtime_variant_preset_values = SearchableField(
        DeploymentRevisionPresetRow.preset_values, None, None
    )
    open_to_public = SearchableField(
        DeploymentRevisionPresetRow.open_to_public,
        BoolConditions(DeploymentRevisionPresetRow.open_to_public),
        ColumnOrder(DeploymentRevisionPresetRow.open_to_public),
    )
    replica_count = SearchableField(
        DeploymentRevisionPresetRow.replica_count,
        IntConditions(DeploymentRevisionPresetRow.replica_count),
        ColumnOrder(DeploymentRevisionPresetRow.replica_count),
    )
    revision_history_limit = SearchableField(
        DeploymentRevisionPresetRow.revision_history_limit,
        IntConditions(DeploymentRevisionPresetRow.revision_history_limit),
        ColumnOrder(DeploymentRevisionPresetRow.revision_history_limit),
    )
    deployment_strategy = SearchableField(
        DeploymentRevisionPresetRow.deployment_strategy,
        EnumConditions(DeploymentRevisionPresetRow.deployment_strategy, DeploymentStrategy),
        ColumnOrder(DeploymentRevisionPresetRow.deployment_strategy),
    )
    deployment_strategy_spec = SearchableField(
        DeploymentRevisionPresetRow.deployment_strategy_spec, None, None
    )
    created_at = SearchableField(
        DeploymentRevisionPresetRow.created_at,
        DateTimeConditions(DeploymentRevisionPresetRow.created_at),
        ColumnOrder(DeploymentRevisionPresetRow.created_at),
    )
    updated_at = SearchableField(
        DeploymentRevisionPresetRow.updated_at,
        DateTimeConditions(DeploymentRevisionPresetRow.updated_at),
        ColumnOrder(DeploymentRevisionPresetRow.updated_at),
    )

    @override
    def to_data(self, row: DeploymentRevisionPresetRow) -> DeploymentRevisionPresetData:
        return DeploymentRevisionPresetData(
            id=self.id.read(row),
            runtime_variant_id=self.runtime_variant_id.read(row),
            name=self.name.read(row),
            description=self.description.read(row),
            rank=self.rank.read(row),
            image_id=self.image_id.read(row),
            model_definition=self.model_definition.read(row),
            resource_opts=[
                ResourceOptsEntryData(name=entry.name, value=entry.value)
                for entry in (self.resource_opts.read(row) or [])
            ],
            cluster_mode=self.cluster_mode.read(row),
            cluster_size=self.cluster_size.read(row),
            startup_command=self.startup_command.read(row),
            bootstrap_script=self.bootstrap_script.read(row),
            environ=[
                EnvironEntryData(key=key, value=value)
                for key, value in (self.environ.read(row) or {}).items()
            ],
            runtime_variant_preset_values=[
                RuntimeVariantPresetValueData(preset_id=entry.preset_id, value=entry.value)
                for entry in (self.runtime_variant_preset_values.read(row) or [])
            ],
            open_to_public=self.open_to_public.read(row),
            replica_count=self.replica_count.read(row),
            revision_history_limit=self.revision_history_limit.read(row),
            deployment_strategy=self.deployment_strategy.read(row),
            deployment_strategy_spec=dict(self.deployment_strategy_spec.read(row)),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


def _meets_every_minimum() -> sa.sql.expression.ColumnElement[bool]:
    """The outer preset carries a slot row for every minimum the joined card requires.

    Relational division: no required slot lacks a slot row whose quantity meets the
    minimum. Each EXISTS correlates against the rows already in the enclosing FROM,
    without which SQLAlchemy aliases the inner FROM and the predicates degenerate into
    Cartesian matches that accept every preset.
    """
    preset = DeploymentRevisionPresetRow.__table__
    card = ModelCardRow.__table__
    requirement = ModelCardResourceRequirementRow.__table__
    slot = PresetResourceSlotRow.__table__
    return ~sa.exists(
        sa.select(sa.literal(1))
        .select_from(requirement)
        .correlate(preset, card)
        .where(
            requirement.c.model_card_id == card.c.id,
            ~sa.exists(
                sa.select(sa.literal(1))
                .select_from(slot)
                .correlate(preset, requirement)
                .where(
                    slot.c.preset_id == preset.c.id,
                    slot.c.slot_name == requirement.c.slot_name,
                    slot.c.quantity >= requirement.c.min_quantity,
                )
            ),
        )
    )


class _DeploymentPresetUsage:
    """Uses between a preset and other entities."""

    model_cards = UsedByConditions[ModelCardID](
        ToManyCorrelation(
            ModelCardRow.__table__,
            DeploymentRevisionPresetRow.__table__,
            _meets_every_minimum(),
        ),
        ModelCardRow.__table__.c.id,
    )
    """Presets a model card can be deployed on: those meeting every minimum slot
    quantity it requires."""

    deployments = UsedByConditions[DeploymentID](
        ToManyCorrelation(
            DeploymentRevisionRow,
            DeploymentRevisionPresetRow,
            DeploymentRevisionRow.revision_preset_id == DeploymentRevisionPresetRow.id,
        ),
        DeploymentRevisionRow.endpoint,
    )
    """Presets a deployment's revisions name."""


class _DeploymentPresetLinkedEntities:
    """How a preset connects to other entities; the other entity's permission governs."""

    usage = _DeploymentPresetUsage


class DeploymentPresetSearchableFields:
    own = _DeploymentPresetOwnFields()
    linked = _DeploymentPresetLinkedEntities
