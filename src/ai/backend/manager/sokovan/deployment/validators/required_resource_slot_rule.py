"""Required resource-slot validator.

Required slot names come from ``resource_slot_types.required``. Both
entry points project their respective input shape to a normalized
:class:`ResourceSlot` and fail when any globally-required slot is
absent or non-positive:

- v2 path: ``DeploymentRevisionCreatorSpec.resource_slots`` is already
  a :class:`ResourceSlot`.
- legacy path: ``ModelRevisionSpec.resource_spec.resource_slots`` is a
  raw mapping; we wrap it in :class:`ResourceSlot` here.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import override

from ai.backend.common.types import ResourceSlot, SlotName
from ai.backend.manager.data.deployment.types import ModelRevisionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.deployment.creators.revision import (
    DeploymentRevisionCreatorSpec,
)
from ai.backend.manager.sokovan.deployment.validators.base import (
    DeploymentRevisionValidationContext,
    DeploymentRevisionValidatorRule,
)


class RequiredResourceSlotRule(DeploymentRevisionValidatorRule):
    """A finalized revision spec must include all globally required slots."""

    @override
    def name(self) -> str:
        return "required_resource_slot"

    @override
    def validate(
        self,
        spec: DeploymentRevisionCreatorSpec,
        context: DeploymentRevisionValidationContext,
    ) -> None:
        self._check_resource_slots(spec.resource_slots, context.required_slot_names)

    @override
    def validate_legacy_revision_spec(
        self,
        spec: ModelRevisionSpec,
        context: DeploymentRevisionValidationContext,
    ) -> None:
        self._check_resource_slots(
            ResourceSlot(spec.resource_spec.resource_slots),
            context.required_slot_names,
        )

    def _check_resource_slots(
        self,
        resource_slots: ResourceSlot,
        required_slot_names: Iterable[SlotName],
    ) -> None:
        if not required_slot_names:
            return
        missing = sorted(
            str(slot_name)
            for slot_name in required_slot_names
            if resource_slots.get(str(slot_name), Decimal(0)) <= Decimal(0)
        )
        if missing:
            raise InvalidAPIParameters(
                extra_msg=(f"resource_slots is missing required resource slot(s): {missing}.")
            )
