from __future__ import annotations

import uuid

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.manager.api.gql.idle_checker.types import (
    IdleCheckerSpecInputGQL,
    PurgeIdleCheckerInputGQL,
    SessionLifetimeIdleCheckerSpecInputGQL,
    UpdateIdleCheckerInputGQL,
)
from ai.backend.manager.api.gql.schema import schema


class TestIdleCheckerInputs:
    def test_one_of_spec_converts_to_dto(self) -> None:
        input_ = IdleCheckerSpecInputGQL(
            session_lifetime=SessionLifetimeIdleCheckerSpecInputGQL(max_lifetime_seconds=3600)
        )

        dto = input_.to_pydantic()

        assert dto.session_lifetime is not None
        assert dto.session_lifetime.max_lifetime_seconds == 3600

    def test_update_omission_and_null_remain_distinct(self) -> None:
        idle_checker_id = uuid.uuid4()

        omitted = UpdateIdleCheckerInputGQL(id=idle_checker_id).to_pydantic()
        cleared = UpdateIdleCheckerInputGQL(id=idle_checker_id, description=None).to_pydantic()

        assert omitted.description is SENTINEL
        assert cleared.description is None

    def test_purge_id_converts_to_dto(self) -> None:
        idle_checker_id = uuid.uuid4()

        dto = PurgeIdleCheckerInputGQL(id=idle_checker_id).to_pydantic()

        assert dto.id == idle_checker_id


class TestIdleCheckerSchemaRegistration:
    def test_admin_operations_and_one_of_are_exposed(self) -> None:
        sdl = schema.as_str()

        assert "adminIdleCheckers(" in sdl
        assert "adminCreateIdleChecker(input: CreateIdleCheckerInput!)" in sdl
        assert "adminUpdateIdleChecker(input: UpdateIdleCheckerInput!)" in sdl
        assert "adminPurgeIdleChecker(input: PurgeIdleCheckerInput!)" in sdl
        assert "input IdleCheckerSpecInput @oneOf" in sdl
        assert "  scopedIdleCheckers(" not in sdl
        assert "  createIdleChecker(" not in sdl
