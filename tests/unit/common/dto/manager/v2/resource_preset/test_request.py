"""Tests for ai.backend.common.dto.manager.v2.resource_preset.request module."""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.v2.common import BinarySizeInput, ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.resource_preset.request import UpdateResourcePresetInput
from ai.backend.common.tristate.unset import UNSET, Unset


class TestUpdateResourcePresetInput:
    """Tests for UpdateResourcePresetInput Unset defaults."""

    def test_omitted_fields_default_to_unset(self) -> None:
        inp = UpdateResourcePresetInput(id=uuid.uuid4())
        assert isinstance(inp.name, Unset)
        assert isinstance(inp.resource_slots, Unset)
        assert isinstance(inp.shared_memory, Unset)
        assert isinstance(inp.resource_group_name, Unset)

    def test_explicit_none_stays_none(self) -> None:
        inp = UpdateResourcePresetInput(
            id=uuid.uuid4(),
            name=None,
            resource_slots=None,
            shared_memory=None,
            resource_group_name=None,
        )
        assert inp.name is None
        assert inp.resource_slots is None
        assert inp.shared_memory is None
        assert inp.resource_group_name is None

    def test_explicit_values_are_kept(self) -> None:
        inp = UpdateResourcePresetInput(
            id=uuid.uuid4(),
            name="preset",
            resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="2")],
            shared_memory=BinarySizeInput(expr="1g"),
            resource_group_name="default",
        )
        assert inp.name == "preset"
        assert inp.resource_slots is not None and not isinstance(inp.resource_slots, Unset)
        assert inp.resource_slots[0].resource_type == "cpu"
        assert inp.shared_memory is not None and not isinstance(inp.shared_memory, Unset)
        assert inp.resource_group_name == "default"

    def test_unset_dropped_from_serialized_payload(self) -> None:
        inp = UpdateResourcePresetInput(id=uuid.uuid4(), name="preset")
        assert inp.name is not UNSET
        dumped = inp.model_dump(exclude_unset=True)
        assert set(dumped) == {"id", "name"}
