"""Resource group allow files are one kind per relation, each written with the creator
its API uses."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from ai.backend.common.types import AccessKey
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.models.resource_group.creators import (
    ResourceGroupForDomainRelationCreator,
    ResourceGroupForKeypairRelationCreator,
    ResourceGroupForProjectRelationCreator,
)
from ai.backend.manager.seed.base import SeedRelationItem
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.resource_group_allow.seed import (
    ResourceGroupForDomainSeed,
    ResourceGroupForKeypairSeed,
    ResourceGroupForProjectSeed,
)
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_DOMAIN = "0198a5a0-0000-7000-8000-0000000a0001"
_PROJECT = "0198a5a0-0000-7000-8000-0000000d0001"
_USER = "0198a5a0-0000-7000-8000-0000000c0001"
_RESOURCE_GROUP = "0198a5a0-0000-7000-8000-0000000e0001"
_OTHER_RESOURCE_GROUP = "0198a5a0-0000-7000-8000-0000000e0002"
_ACCESS_KEY = AccessKey("AKIAMEMBER0000000000")


def _write(path: Path, kind: SeedKind, *items: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": str(kind), "version": 1, "items": list(items)}))
    return path


class TestResourceGroupForDomainSeed:
    def test_the_domain_is_the_scope_and_the_resource_group_the_target(self) -> None:
        seed = ResourceGroupForDomainSeed.model_validate({
            "domain_id": _DOMAIN,
            "resource_group_id": _RESOURCE_GROUP,
        })
        write = seed.write()
        assert isinstance(write.creator, ResourceGroupForDomainRelationCreator)
        assert (str(write.scope), str(write.target)) == (_DOMAIN, _RESOURCE_GROUP)
        assert seed.key() == f"{_DOMAIN}:{_RESOURCE_GROUP}"


class TestResourceGroupForProjectSeed:
    def test_the_project_is_the_scope_and_the_resource_group_the_target(self) -> None:
        seed = ResourceGroupForProjectSeed.model_validate({
            "project_id": _PROJECT,
            "resource_group_id": _RESOURCE_GROUP,
        })
        write = seed.write()
        assert isinstance(write.creator, ResourceGroupForProjectRelationCreator)
        assert (str(write.scope), str(write.target)) == (_PROJECT, _RESOURCE_GROUP)
        assert seed.key() == f"{_PROJECT}:{_RESOURCE_GROUP}"


class TestResourceGroupForKeypairSeed:
    def test_the_owner_is_the_scope_and_the_key_names_the_row(self) -> None:
        seed = ResourceGroupForKeypairSeed.model_validate({
            "access_key": _ACCESS_KEY,
            "user_id": _USER,
            "resource_group_id": _RESOURCE_GROUP,
        })
        write = seed.write()
        assert write.creator == ResourceGroupForKeypairRelationCreator(access_key=_ACCESS_KEY)
        assert (str(write.scope), str(write.target)) == (_USER, _RESOURCE_GROUP)
        assert seed.key() == f"{_ACCESS_KEY}:{_RESOURCE_GROUP}"

    def test_an_item_without_the_owner_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            ResourceGroupForKeypairSeed.model_validate({
                "access_key": _ACCESS_KEY,
                "resource_group_id": _RESOURCE_GROUP,
            })

    def test_an_access_key_longer_than_the_column_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            ResourceGroupForKeypairSeed.model_validate({
                "access_key": "A" * 21,
                "user_id": _USER,
                "resource_group_id": _RESOURCE_GROUP,
            })


class TestKind:
    @pytest.mark.parametrize(
        "kind",
        [
            SeedKind.RESOURCE_GROUP_FOR_DOMAIN,
            SeedKind.RESOURCE_GROUP_FOR_PROJECT,
            SeedKind.RESOURCE_GROUP_FOR_KEYPAIR,
        ],
    )
    def test_each_kind_is_a_relation_applied_after_every_entity_kind(self, kind: SeedKind) -> None:
        ordered = create_seed_kind_registry().ordered()
        names = [model.name for model in ordered]
        entity_kinds = [
            model.name for model in ordered if not issubclass(model.model, SeedRelationItem)
        ]
        assert names.index(kind) > names.index(entity_kinds[-1])

    def test_an_unknown_field_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            ResourceGroupForDomainSeed.model_validate({
                "domain_id": _DOMAIN,
                "resource_group_id": _RESOURCE_GROUP,
                "is_active": True,
            })

    def test_a_file_repeating_a_pair_is_left_out(self, tmp_path: Path) -> None:
        pair = {"domain_id": _DOMAIN, "resource_group_id": _RESOURCE_GROUP}
        _write(tmp_path / "a.yaml", SeedKind.RESOURCE_GROUP_FOR_DOMAIN, pair)
        _write(
            tmp_path / "b.yaml",
            SeedKind.RESOURCE_GROUP_FOR_DOMAIN,
            pair,
            {"domain_id": _DOMAIN, "resource_group_id": _OTHER_RESOURCE_GROUP},
        )

        plan = SeedPlanner(create_seed_kind_registry()).plan([tmp_path])

        assert plan.batches == []
        assert len(plan.rejections) == 2
