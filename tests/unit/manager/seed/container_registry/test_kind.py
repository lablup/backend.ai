"""The `container_registry` kind reads one item per registry id, and `mgr seed check`
reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.container_registry.seed import ContainerRegistrySeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-00000000c001"
_ITEM: dict[str, Any] = {
    "id": _ID,
    "registry_name": "cr.backend.ai",
    "url": "https://cr.backend.ai",
    "type": "harbor2",
    "project": "stable",
}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "container_registry", "version": 1, "items": list(items)})
    )
    return path


class TestContainerRegistrySeed:
    def test_the_key_is_the_id(self) -> None:
        seed = ContainerRegistrySeed.model_validate(_ITEM)
        assert seed.key() == _ID

    def test_left_out_fields_take_the_column_defaults(self) -> None:
        seed = ContainerRegistrySeed.model_validate({
            "id": _ID,
            "registry_name": "local",
            "url": "http://localhost",
            "type": "local",
        })
        assert seed.is_global is True
        assert seed.ssl_verify is True
        assert seed.project is None

    @pytest.mark.parametrize(
        "change",
        [
            {"id": None},
            {"type": "unknown"},
            {"registry_name": ""},
            {"registry_name": "x" * 256},
            {"url": "https://" + "x" * 512},
            {"url": "https://"},
            {"project": None},
            {"project": "Not_Valid"},
            {"username": "x" * 256},
            {"unknown": True},
        ],
        ids=[
            "missing-id",
            "unknown-type",
            "empty-name",
            "too-long-name",
            "too-long-url",
            "invalid-url",
            "harbor-without-project",
            "invalid-harbor-project",
            "too-long-username",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, change: dict[str, Any]) -> None:
        item = {key: value for key, value in (_ITEM | change).items() if value is not None}
        with pytest.raises(InvalidSeedDocument):
            ContainerRegistrySeed.model_validate(item)


class TestContainerRegistryKind:
    def test_the_files_are_planned_whole(self, container_registry_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([container_registry_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "container_registry"
        assert [item.key() for item in batch.items()] == [
            "0198a5a0-0000-7000-8000-00000000c001",
            "0198a5a0-0000-7000-8000-00000000c002",
        ]

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _ITEM)
        second = _write(tmp_path / "second.yaml", _ITEM | {"project": "community"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, container_registry_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(container_registry_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "container_registry: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _ITEM | {"url": "https://"})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0


class TestContainerRegistrySeedCheck:
    def test_an_item_keeping_the_rules_passes(self) -> None:
        assert ContainerRegistrySeed.model_validate(_ITEM).check() == []

    @pytest.mark.parametrize(
        "item",
        [
            {**_ITEM, "registry_name": "  "},
        ],
        ids=[
            "blank-registry-name",
        ],
    )
    def test_an_item_breaking_a_rule_fails(self, item: dict[str, Any]) -> None:
        assert len(ContainerRegistrySeed.model_validate(item).check()) == 1
