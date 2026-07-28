from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.idle_checker_binding.request import (
    CreateIdleCheckerBindingInput,
    IdleCheckerBindingScopeDTO,
    IdleCheckerScopeRefDTO,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.types import IdleCheckerScopeTypeDTO
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.idle_checker import IdleCheckerID


def _domain_scope_ref() -> IdleCheckerScopeRefDTO:
    return IdleCheckerScopeRefDTO(
        scope_type=IdleCheckerScopeTypeDTO.DOMAIN,
        scope_id="default",
    )


class TestIdleCheckerScopeRef:
    def test_accepts_typed_scope_pair(self) -> None:
        ref = _domain_scope_ref()

        assert ref.scope_type is IdleCheckerScopeTypeDTO.DOMAIN
        assert ref.scope_id == "default"

    def test_rejects_empty_scope_id(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerScopeRefDTO(
                scope_type=IdleCheckerScopeTypeDTO.DOMAIN,
                scope_id="",
            )


class TestIdleCheckerBindingScope:
    def test_rejects_empty_items(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerBindingScopeDTO(items=[])


class TestCreateIdleCheckerBindingInput:
    def test_enabled_defaults_to_true(self) -> None:
        input_ = CreateIdleCheckerBindingInput(
            scope=_domain_scope_ref(),
            idle_checker_id=IdleCheckerID(uuid.uuid4()),
        )

        assert input_.enabled is True
