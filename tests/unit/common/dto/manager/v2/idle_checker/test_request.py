from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.idle_checker.request import (
    CreateIdleCheckerInput,
    IdleCheckerSpecInputDTO,
    SessionLifetimeSpecInputDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker.types import IdleCheckerInputTypeDTO
from ai.backend.common.exception import BackendAISchemaValidationFailed


def _session_lifetime_spec() -> IdleCheckerSpecInputDTO:
    return IdleCheckerSpecInputDTO(
        session_lifetime=SessionLifetimeSpecInputDTO(max_lifetime_seconds=3600)
    )


class TestCreateIdleCheckerInput:
    def test_rejects_empty_target_session_types(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateIdleCheckerInput(
                name="session lifetime",
                checker_type=IdleCheckerInputTypeDTO.SESSION_LIFETIME,
                target_session_types=[],
                checker_spec=_session_lifetime_spec(),
            )

    def test_rejects_missing_spec(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerSpecInputDTO()

    def test_rejects_zero_max_lifetime(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            SessionLifetimeSpecInputDTO(max_lifetime_seconds=0)
