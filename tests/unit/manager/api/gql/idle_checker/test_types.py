from __future__ import annotations

from ai.backend.manager.api.gql.idle_checker.types import (
    IdleCheckerSpecInputGQL,
    SessionLifetimeIdleCheckerSpecInputGQL,
)


class TestIdleCheckerInputs:
    def test_one_of_spec_converts_to_dto(self) -> None:
        input_ = IdleCheckerSpecInputGQL(
            session_lifetime=SessionLifetimeIdleCheckerSpecInputGQL(max_lifetime_seconds=3600)
        )

        dto = input_.to_pydantic()

        assert dto.session_lifetime is not None
        assert dto.session_lifetime.max_lifetime_seconds == 3600
