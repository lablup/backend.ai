from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.idle_checker_binding.request import (
    CreateIdleCheckerBindingInput,
    IdleCheckerBindingScopeDTO,
    ScopedSearchIdleCheckerBindingsInput,
)
from ai.backend.common.dto.manager.v2.idle_checker_binding.types import IdleCheckerScopeTypeDTO
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.idle_checker import IdleCheckerID


def _domain_scope() -> IdleCheckerBindingScopeDTO:
    return IdleCheckerBindingScopeDTO(
        scope_type=IdleCheckerScopeTypeDTO.DOMAIN,
        scope_id="default",
    )


class TestIdleCheckerBindingScope:
    def test_accepts_typed_scope_pair(self) -> None:
        scope = _domain_scope()

        assert scope.scope_type is IdleCheckerScopeTypeDTO.DOMAIN
        assert scope.scope_id == "default"

    def test_rejects_empty_scope_id(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerBindingScopeDTO(
                scope_type=IdleCheckerScopeTypeDTO.DOMAIN,
                scope_id="",
            )


class TestCreateIdleCheckerBindingInput:
    def test_enabled_defaults_to_true(self) -> None:
        input_ = CreateIdleCheckerBindingInput(
            scope=_domain_scope(),
            idle_checker_id=IdleCheckerID(uuid.uuid4()),
        )

        assert input_.enabled is True


class TestScopedSearchIdleCheckerBindingsInput:
    def test_rejects_empty_scope_list(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            ScopedSearchIdleCheckerBindingsInput(scope=[])
