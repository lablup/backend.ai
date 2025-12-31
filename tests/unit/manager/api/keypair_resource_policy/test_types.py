from __future__ import annotations

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.types import OptionalState, _TriStateEnum


class TestModifyKeyPairResourcePolicyInputType:
    def test_empty_total_resource_slots_should_be_updated(self) -> None:
        """
        Regression test: empty dict {} for total_resource_slots should result in UPDATE state.

        Previously, empty dict was treated as falsy and converted to Undefined,
        causing the field to be skipped during updates.
        """
        empty_resource_slot = ResourceSlot.from_user_input({}, None)
        optional_state = OptionalState[ResourceSlot].from_graphql(empty_resource_slot)

        assert optional_state._state == _TriStateEnum.UPDATE
        assert optional_state.value() == ResourceSlot()
