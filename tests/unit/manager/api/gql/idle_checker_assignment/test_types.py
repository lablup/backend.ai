from __future__ import annotations

from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO
from ai.backend.manager.api.gql.idle_checker_assignment.types import (
    IdleCheckerAssignmentScopeGQL,
    IdleCheckerScopeRefGQL,
    IdleCheckerScopeTypeGQL,
)


class TestIdleCheckerAssignmentInputs:
    def test_scope_converts_to_dto(self) -> None:
        input_ = IdleCheckerAssignmentScopeGQL(
            items=[
                IdleCheckerScopeRefGQL(
                    scope_type=IdleCheckerScopeTypeGQL.PROJECT,
                    scope_id="7b56b1f4-2936-4d29-9db9-621cc5b1cf8f",
                ),
            ],
        )

        dto = input_.to_pydantic()

        assert len(dto.items) == 1
        assert dto.items[0].scope_type == IdleCheckerScopeTypeDTO.PROJECT
        assert dto.items[0].scope_id == "7b56b1f4-2936-4d29-9db9-621cc5b1cf8f"
