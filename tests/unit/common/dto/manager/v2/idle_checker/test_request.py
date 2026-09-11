from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    CreateIdleCheckerInput,
    IdleCheckerSpecInputDTO,
    NetworkTimeoutSpecInputDTO,
    SessionLifetimeSpecInputDTO,
    UpdateIdleCheckerInput,
)
from ai.backend.common.dto.manager.v2.idle_checker.types import IdleCheckerInputTypeDTO
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.tristate.unset import UNSET
from ai.backend.common.types import SessionTypes


def _session_lifetime_spec() -> IdleCheckerSpecInputDTO:
    return IdleCheckerSpecInputDTO(
        session_lifetime=SessionLifetimeSpecInputDTO(max_lifetime_seconds=3600)
    )


def _network_spec() -> IdleCheckerSpecInputDTO:
    return IdleCheckerSpecInputDTO(
        network=NetworkTimeoutSpecInputDTO(max_network_inactivity_seconds=600)
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

    def test_rejects_multiple_specs(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerSpecInputDTO(
                session_lifetime=SessionLifetimeSpecInputDTO(max_lifetime_seconds=3600),
                network=NetworkTimeoutSpecInputDTO(max_network_inactivity_seconds=600),
            )

    def test_rejects_checker_type_spec_mismatch(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            CreateIdleCheckerInput(
                name="mismatched",
                checker_type=IdleCheckerInputTypeDTO.SESSION_LIFETIME,
                target_session_types=[SessionTypes.INTERACTIVE],
                checker_spec=_network_spec(),
            )

    def test_rejects_zero_max_lifetime(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            SessionLifetimeSpecInputDTO(max_lifetime_seconds=0)


class TestUpdateIdleCheckerInput:
    def test_omitted_fields_are_unset(self) -> None:
        inp = UpdateIdleCheckerInput(id=IdleCheckerID(uuid4()))
        assert inp.name is UNSET
        assert inp.description is UNSET
        assert inp.target_session_types is UNSET
        assert inp.initial_grace_period_seconds is UNSET
        assert inp.checker_spec is UNSET

    def test_explicit_none_stays_none(self) -> None:
        inp = UpdateIdleCheckerInput(
            id=IdleCheckerID(uuid4()),
            name=None,
            description=None,
            target_session_types=None,
            initial_grace_period_seconds=None,
            checker_spec=None,
        )
        assert inp.name is None
        assert inp.description is None
        assert inp.target_session_types is None
        assert inp.initial_grace_period_seconds is None
        assert inp.checker_spec is None

    def test_values_are_kept(self) -> None:
        spec = _session_lifetime_spec()
        inp = UpdateIdleCheckerInput(
            id=IdleCheckerID(uuid4()),
            name="renamed",
            target_session_types=[SessionTypes.BATCH],
            initial_grace_period_seconds=30,
            checker_spec=spec,
        )
        assert inp.name == "renamed"
        assert inp.target_session_types == [SessionTypes.BATCH]
        assert inp.initial_grace_period_seconds == 30
        assert inp.checker_spec is spec

    def test_rejects_empty_name(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateIdleCheckerInput(id=IdleCheckerID(uuid4()), name="")

    def test_rejects_empty_target_session_types(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateIdleCheckerInput(id=IdleCheckerID(uuid4()), target_session_types=[])

    def test_rejects_negative_grace_period(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            UpdateIdleCheckerInput(id=IdleCheckerID(uuid4()), initial_grace_period_seconds=-1)
