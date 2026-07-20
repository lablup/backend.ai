"""Query conditions for deployment revision preset rows."""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    PresetResourceSlotRow,
)

__all__ = ("DeploymentRevisionPresetConditions",)


class DeploymentRevisionPresetConditions:
    @staticmethod
    def by_runtime_variant_id(variant_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionPresetRow.runtime_variant == variant_id

        return inner

    @staticmethod
    def by_runtime_variant_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = DeploymentRevisionPresetRow.runtime_variant == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_runtime_variant_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = DeploymentRevisionPresetRow.runtime_variant.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionPresetRow.name.ilike(f"%{spec.value}%")
            else:
                condition = DeploymentRevisionPresetRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DeploymentRevisionPresetRow.name) == spec.value.lower()
            else:
                condition = DeploymentRevisionPresetRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionPresetRow.name.ilike(f"{spec.value}%")
            else:
                condition = DeploymentRevisionPresetRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionPresetRow.name.ilike(f"%{spec.value}")
            else:
                condition = DeploymentRevisionPresetRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(DeploymentRevisionPresetRow.name))

    @staticmethod
    def by_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = DeploymentRevisionPresetRow.id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = DeploymentRevisionPresetRow.id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_model_card_compatible(model_card_id: UUID) -> QueryCondition:
        """Match presets whose resource slots satisfy every ``min_resource`` requirement
        of the given model card.

        Relational division: a preset is compatible iff for every required slot in the
        card's ``model_card_resource_requirements`` there exists a matching
        ``preset_resource_slots`` row whose quantity meets the requirement. Returns the
        same set as ``ModelCardV2.availablePresets`` for that card.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            mcr = ModelCardResourceRequirementRow.__table__
            prs = PresetResourceSlotRow.__table__
            drp = DeploymentRevisionPresetRow.__table__
            # Both sub-EXISTS clauses must correlate against the outer drp/mcr,
            # otherwise SQLAlchemy injects fresh aliases into the inner FROM clause
            # and the predicates degenerate into Cartesian-product matches that
            # accept every preset.
            return ~sa.exists(
                sa.select(sa.literal(1))
                .select_from(mcr)
                .correlate(drp)
                .where(
                    mcr.c.model_card_id == model_card_id,
                    ~sa.exists(
                        sa.select(sa.literal(1))
                        .select_from(prs)
                        .correlate(drp, mcr)
                        .where(
                            prs.c.preset_id == drp.c.id,
                            prs.c.slot_name == mcr.c.slot_name,
                            prs.c.quantity >= mcr.c.min_quantity,
                        )
                    ),
                )
            )

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionPresetRow.id < sa.text(f"'{cursor_id}'::uuid")

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionPresetRow.id > sa.text(f"'{cursor_id}'::uuid")

        return inner
