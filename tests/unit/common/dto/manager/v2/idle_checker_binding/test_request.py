from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.idle_checker_binding.request import (
    CreateIdleCheckerBindingInput,
    IdleCheckerBindingScopeDTO,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.project import ProjectID


class TestIdleCheckerBindingScope:
    def test_accepts_single_scope(self) -> None:
        domain_id = DomainID(uuid.uuid4())

        scope = IdleCheckerBindingScopeDTO(domain=domain_id)

        assert scope.domain == domain_id
        assert scope.project is None
        assert scope.resource_group is None

    def test_rejects_empty_scope(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerBindingScopeDTO()

    def test_rejects_multiple_scopes(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            IdleCheckerBindingScopeDTO(
                domain=DomainID(uuid.uuid4()),
                project=ProjectID(uuid.uuid4()),
            )


class TestCreateIdleCheckerBindingInput:
    def test_options_default_to_none(self) -> None:
        input_ = CreateIdleCheckerBindingInput(
            scope=IdleCheckerBindingScopeDTO(domain=DomainID(uuid.uuid4())),
            idle_checker_id=IdleCheckerID(uuid.uuid4()),
        )

        assert input_.options is None
