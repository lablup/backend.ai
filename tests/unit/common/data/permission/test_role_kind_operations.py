"""Tests for the per-entity allowed-operation cached helper."""

from __future__ import annotations

import pytest

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import OperationType, member_operations

_READ_ONLY_OPS: frozenset[OperationType] = frozenset({OperationType.READ})
_READ_AND_CREATE_OPS: frozenset[OperationType] = frozenset({
    OperationType.READ,
    OperationType.CREATE,
})

_MEMBER_CREATE_ENTITIES: list[EntityType] = [
    SessionEntityType(),
    VFolderEntityType(),
    DeploymentEntityType(),
]
_OTHER_ENTITIES: list[EntityType] = [
    AgentEntityType(),
    DomainEntityType(),
    UserEntityType(),
]


class TestDefaultFallback:
    """Entity types the helper does not name fall back to read only."""

    @pytest.mark.parametrize("entity_type", _OTHER_ENTITIES)
    def test_member_fallback_is_read_only(self, entity_type: EntityType) -> None:
        assert member_operations(entity_type) == _READ_ONLY_OPS


class TestMemberCreateOverrides:
    """Members may CREATE sessions, vfolders and model deployments in their scope."""

    @pytest.mark.parametrize("entity_type", _MEMBER_CREATE_ENTITIES)
    def test_member_can_create(self, entity_type: EntityType) -> None:
        assert member_operations(entity_type) == _READ_AND_CREATE_OPS


class TestPurity:
    """The helper is a pure function of its argument."""

    def test_member_is_pure(self) -> None:
        first = member_operations(SessionEntityType())
        member_operations(VFolderEntityType())
        assert member_operations(SessionEntityType()) == first
