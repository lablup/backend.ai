from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    CreateIdleCheckerInput,
    IdleCheckerSpecInputDTO,
    PurgeIdleCheckerInput,
    SessionLifetimeSpecInputDTO,
    UpdateIdleCheckerInput,
)
from ai.backend.common.dto.manager.v2.idle_checker.types import IdleCheckerInputTypeDTO
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionTypes


def _session_lifetime_spec() -> IdleCheckerSpecInputDTO:
    return IdleCheckerSpecInputDTO(
        session_lifetime=SessionLifetimeSpecInputDTO(max_lifetime_seconds=3600)
    )


class TestCreateIdleCheckerInput:
    def test_description_is_optional(self) -> None:
        input_ = CreateIdleCheckerInput(
            name="session lifetime",
            checker_type=IdleCheckerInputTypeDTO.SESSION_LIFETIME,
            target_session_types=[SessionTypes.INTERACTIVE],
            checker_spec=_session_lifetime_spec(),
        )

        assert input_.description is None

    def test_rejects_empty_target_session_types(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateIdleCheckerInput(
                name="session lifetime",
                checker_type=IdleCheckerInputTypeDTO.SESSION_LIFETIME,
                target_session_types=[],
                checker_spec=_session_lifetime_spec(),
            )


class TestIdleCheckerSpecInput:
    def test_rejects_missing_spec(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerSpecInputDTO()

    def test_rejects_negative_max_lifetime(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            SessionLifetimeSpecInputDTO(max_lifetime_seconds=-1)


class TestUpdateIdleCheckerInput:
    def test_omitted_description_uses_sentinel(self) -> None:
        input_ = UpdateIdleCheckerInput(id=IdleCheckerID(uuid.uuid4()))

        assert input_.description is SENTINEL

    def test_null_description_clears_value(self) -> None:
        input_ = UpdateIdleCheckerInput(id=IdleCheckerID(uuid.uuid4()), description=None)

        assert input_.description is None


class TestPurgeIdleCheckerInput:
    def test_accepts_id(self) -> None:
        idle_checker_id = IdleCheckerID(uuid.uuid4())

        input_ = PurgeIdleCheckerInput(id=idle_checker_id)

        assert input_.id == idle_checker_id
