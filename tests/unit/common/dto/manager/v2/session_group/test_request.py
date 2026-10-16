"""Unit tests for session_group request DTO validation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ai.backend.common.dto.manager.v2.session_group.request import UpdateSessionGroupInput
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed, InvalidAPIParameters
from ai.backend.common.tristate.unset import UNSET


class TestUpdateSessionGroupInput:
    def test_omitted_field_is_unset(self) -> None:
        inp = UpdateSessionGroupInput.model_validate({
            "id": str(uuid4()),
            "placement_direction": "spread",
        })
        assert inp.placement_direction == SessionGroupPlacementDirectionEnum.SPREAD
        assert inp.placement_enforcement is UNSET

    def test_both_fields_are_kept(self) -> None:
        inp = UpdateSessionGroupInput(
            id=uuid4(),
            placement_direction=SessionGroupPlacementDirectionEnum.PACK,
            placement_enforcement=SessionGroupPlacementEnforcementEnum.PREFERRED,
        )
        assert inp.placement_direction == SessionGroupPlacementDirectionEnum.PACK
        assert inp.placement_enforcement == SessionGroupPlacementEnforcementEnum.PREFERRED

    @pytest.mark.parametrize(
        "body",
        [
            {},
            {"placement_direction": None, "placement_enforcement": None},
        ],
        ids=["both-omitted", "both-null"],
    )
    def test_an_input_changing_nothing_is_rejected(self, body: dict[str, None]) -> None:
        with pytest.raises(InvalidAPIParameters):
            UpdateSessionGroupInput.model_validate({"id": str(uuid4()), **body})

    def test_an_unknown_direction_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            UpdateSessionGroupInput.model_validate({
                "id": str(uuid4()),
                "placement_direction": "sideways",
            })
