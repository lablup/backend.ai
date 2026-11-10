"""The scoped audit log query validates the entity type an entity scope item names."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.api.gql.audit_log.types.scope import AuditLogScopeGQL
from ai.backend.manager.api.gql.rbac.types.scope import EntityTypeScopeGQL


def _scope(entity_type: str) -> AuditLogScopeGQL:
    return AuditLogScopeGQL(
        entity=[EntityTypeScopeGQL(entity_type=entity_type, entity_id=str(uuid.uuid4()))],
    )


def test_entity_type_differing_only_in_case_resolves_to_the_kind() -> None:
    scope = _scope("VFOLDER").to_pydantic()
    assert scope.entity is not None
    assert type(scope.entity[0].entity_type) is VFolderEntityType


def test_undeclared_entity_type_is_an_input_error() -> None:
    with pytest.raises(ValidationError):
        _scope("vfolder:data").to_pydantic()
