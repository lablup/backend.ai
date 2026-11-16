from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.container_registry.creators import ContainerRegistryProjectCreator
from ai.backend.manager.models.container_registry.purgers import ContainerRegistryProjectPurger
from ai.backend.manager.services.rbac.actions.relation.base import RelationPair
from ai.backend.manager.services.rbac.actions.relation.update import UpdateRelationAction
from ai.backend.manager.services.rbac.service import RbacRelationService


class TestUpdate:
    async def test_a_pair_named_on_both_sides_is_rejected_before_writing(self) -> None:
        repository = AsyncMock()
        pair = RelationPair(scope=ProjectID(uuid.uuid4()), target=ContainerRegistryID(uuid.uuid4()))

        with pytest.raises(InvalidAPIParameters):
            await RbacRelationService(repository).update(
                UpdateRelationAction(
                    create_pairs=[pair],
                    creator=ContainerRegistryProjectCreator(),
                    purge_pairs=[pair],
                    purger=ContainerRegistryProjectPurger(),
                )
            )

        repository.update.assert_not_awaited()
