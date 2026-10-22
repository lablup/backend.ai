"""The `container_registry_project` kind reads one item per registry and project pair,
and is applied after every entity kind."""

from __future__ import annotations

from typing import Any

import pytest

from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.models.container_registry.creators import ContainerRegistryProjectCreator
from ai.backend.manager.seed.base import SeedRelationItem
from ai.backend.manager.seed.container_registry_project.seed import ContainerRegistryProjectSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.types import SeedKind

_REGISTRY = "0198a5a0-0000-7000-8000-00000000c001"
_PROJECT = "0198a5a0-0000-7000-8000-00000000d001"
_ITEM: dict[str, Any] = {"registry_id": _REGISTRY, "project_id": _PROJECT}


class TestContainerRegistryProjectSeed:
    def test_the_key_joins_both_ids(self) -> None:
        seed = ContainerRegistryProjectSeed.model_validate(_ITEM)
        assert seed.key() == f"{_REGISTRY}:{_PROJECT}"

    @pytest.mark.parametrize("is_default", [False, True])
    def test_the_item_is_written_with_the_creator_the_api_uses(self, is_default: bool) -> None:
        seed = ContainerRegistryProjectSeed.model_validate({**_ITEM, "is_default": is_default})
        write = seed.write()
        assert write.creator == ContainerRegistryProjectCreator(is_default=is_default)
        assert str(write.scope) == _PROJECT
        assert str(write.target) == _REGISTRY

    def test_a_left_out_default_is_false(self) -> None:
        assert ContainerRegistryProjectSeed.model_validate(_ITEM).is_default is False

    @pytest.mark.parametrize(
        "change",
        [{"registry_id": None}, {"project_id": "not-a-uuid"}, {"unknown": 1}],
        ids=["missing-registry", "invalid-project", "unknown-field"],
    )
    def test_an_invalid_item_is_refused(self, change: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            ContainerRegistryProjectSeed.model_validate({**_ITEM, **change})


class TestKindOrder:
    def test_the_kind_is_applied_after_every_entity_kind(self) -> None:
        ordered = create_seed_kind_registry().ordered()
        names = [model.name for model in ordered]
        entity_kinds = [
            model.name for model in ordered if not issubclass(model.model, SeedRelationItem)
        ]
        assert names.index(SeedKind.CONTAINER_REGISTRY_PROJECT) > names.index(entity_kinds[-1])
