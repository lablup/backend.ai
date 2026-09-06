"""The v2 RBAC bundle has to reach every slot the processors read."""

from __future__ import annotations

import dataclasses

from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import VirtualEntityRBACValidators
from ai.backend.testutils.action_validators import mock_virtual_entity_rbac_validators


class TestVirtualEntityRBACValidatorWiring:
    def test_every_bundled_validator_reaches_a_slot(self) -> None:
        bundle = mock_virtual_entity_rbac_validators()
        slots = bundle.to_action_validators()
        wired = [
            validator
            for slot in dataclasses.fields(ActionValidators)
            for validator in getattr(slots, slot.name)
        ]

        for bundled_field in dataclasses.fields(VirtualEntityRBACValidators):
            validator = getattr(bundle, bundled_field.name)
            assert any(validator is entry for entry in wired), (
                f"{bundled_field.name} validator is not wired into any slot"
            )

    def test_slots_hold_their_own_shape(self) -> None:
        bundle = mock_virtual_entity_rbac_validators()
        validators = bundle.to_action_validators()

        assert validators.single_entity == [bundle.single_entity]
        assert validators.partial_bulk == [bundle.partial_bulk]
        assert validators.atomic_bulk == [bundle.atomic_bulk]
        assert validators.scope == [bundle.scope]
        assert validators.relation == [bundle.relation]
