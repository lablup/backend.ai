from __future__ import annotations

from ai.backend.common.dto.manager.v2.idle_checker_binding.types import IdleCheckerScopeTypeDTO
from ai.backend.manager.api.gql.idle_checker_binding.types import (
    IdleCheckerBindingScopeGQL,
    IdleCheckerScopeTypeGQL,
)


class TestIdleCheckerBindingInputs:
    def test_scope_pair_converts_to_dto(self) -> None:
        input_ = IdleCheckerBindingScopeGQL(
            scope_type=IdleCheckerScopeTypeGQL.PROJECT,
            scope_id="7b56b1f4-2936-4d29-9db9-621cc5b1cf8f",
        )

        dto = input_.to_pydantic()

        assert dto.scope_type == IdleCheckerScopeTypeDTO.PROJECT
        assert dto.scope_id == "7b56b1f4-2936-4d29-9db9-621cc5b1cf8f"
