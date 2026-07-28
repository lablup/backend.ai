from __future__ import annotations

import uuid

from ai.backend.manager.api.gql.idle_checker_binding.types import (
    IdleCheckerBindingOptionsInputGQL,
    IdleCheckerBindingScopeGQL,
)


class TestIdleCheckerBindingInputs:
    def test_one_of_scope_converts_to_dto(self) -> None:
        domain_id = uuid.uuid4()

        input_ = IdleCheckerBindingScopeGQL(domain=domain_id)

        dto = input_.to_pydantic()

        assert dto.domain == domain_id
        assert dto.project is None
        assert dto.resource_group is None

    def test_options_input_converts_to_dto(self) -> None:
        input_ = IdleCheckerBindingOptionsInputGQL(enabled=False)

        dto = input_.to_pydantic()

        assert dto.enabled is False
