"""Unit tests for session_group request DTO validation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ai.backend.common.dto.manager.v2.session_group.request import (
    CreateSessionGroupInput,
    UpdateSessionGroupInput,
)
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupAdmissionEnum,
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
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
        with pytest.raises(BackendAISchemaValidationFailed):
            UpdateSessionGroupInput.model_validate({"id": str(uuid4()), **body})

    def test_an_unknown_direction_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            UpdateSessionGroupInput.model_validate({
                "id": str(uuid4()),
                "placement_direction": "sideways",
            })

    def test_an_admission_change_alone_is_kept(self) -> None:
        inp = UpdateSessionGroupInput.model_validate({
            "id": str(uuid4()),
            "admission": "all_or_none",
            "member_count": 4,
        })
        assert inp.admission == SessionGroupAdmissionEnum.ALL_OR_NONE
        assert inp.member_count == 4

    def test_clearing_the_member_count_is_a_change(self) -> None:
        inp = UpdateSessionGroupInput.model_validate({"id": str(uuid4()), "member_count": None})
        assert inp.member_count is None

    def test_a_member_count_below_two_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            UpdateSessionGroupInput.model_validate({"id": str(uuid4()), "member_count": 1})


class TestCreateSessionGroupInput:
    def _body(self, **admission: object) -> dict[str, object]:
        return {
            "project_id": str(uuid4()),
            "placement_direction": "spread",
            "placement_enforcement": "strict",
            **admission,
        }

    def test_admission_defaults_to_independent(self) -> None:
        inp = CreateSessionGroupInput.model_validate(self._body())
        assert inp.admission == SessionGroupAdmissionEnum.INDEPENDENT
        assert inp.member_count is None

    def test_an_all_or_none_group_takes_its_member_count(self) -> None:
        inp = CreateSessionGroupInput.model_validate(
            self._body(admission="all_or_none", member_count=3)
        )
        assert inp.member_count == 3

    @pytest.mark.parametrize(
        "admission",
        [
            {"admission": "all_or_none"},
            {"admission": "all_or_none", "member_count": 1},
            {"admission": "independent", "member_count": 3},
        ],
        ids=["all-or-none-without-count", "count-below-two", "independent-with-count"],
    )
    def test_a_member_count_not_matching_the_admission_is_rejected(
        self, admission: dict[str, object]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            CreateSessionGroupInput.model_validate(self._body(**admission))
