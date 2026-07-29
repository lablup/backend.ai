from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    CreateIdleCheckerAssignmentInput,
    IdleCheckerAssignmentScopeDTO,
    IdleCheckerScopeRefDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.idle_checker import IdleCheckerID

_DOMAIN_SCOPE_ID = uuid.UUID("7b56b1f4-2936-4d29-9db9-621cc5b1cf8f")


def _domain_scope_ref() -> IdleCheckerScopeRefDTO:
    return IdleCheckerScopeRefDTO(
        scope_type=IdleCheckerScopeTypeDTO.DOMAIN,
        scope_id=_DOMAIN_SCOPE_ID,
    )


class TestIdleCheckerScopeRef:
    def test_accepts_typed_scope_pair(self) -> None:
        ref = _domain_scope_ref()

        assert ref.scope_type is IdleCheckerScopeTypeDTO.DOMAIN
        assert ref.scope_id == _DOMAIN_SCOPE_ID

    def test_rejects_non_uuid_scope_id(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerScopeRefDTO.model_validate({
                "scope_type": IdleCheckerScopeTypeDTO.DOMAIN,
                "scope_id": "default",
            })


class TestIdleCheckerAssignmentScope:
    def test_rejects_empty_items(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerAssignmentScopeDTO(items=[])


class TestCreateIdleCheckerAssignmentInput:
    def test_enabled_defaults_to_true(self) -> None:
        input_ = CreateIdleCheckerAssignmentInput(
            scope=_domain_scope_ref(),
            idle_checker_id=IdleCheckerID(uuid.uuid4()),
        )

        assert input_.enabled is True
