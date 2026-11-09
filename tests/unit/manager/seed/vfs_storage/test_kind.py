"""The `vfs_storage` kind reads one item per storage id, and `mgr seed check` reports
what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.vfs_storage.seed import VFSStorageSeed

_ID = "0198a5a0-0000-7000-8000-00000000b001"
_ITEM: dict[str, Any] = {"id": _ID, "name": "local", "host": "local", "base_path": "/vfs"}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "vfs_storage", "version": 1, "items": list(items)}))
    return path


class TestVFSStorageSeed:
    def test_the_key_is_the_id(self) -> None:
        assert VFSStorageSeed.model_validate(_ITEM).key() == _ID

    @pytest.mark.parametrize(
        "item",
        [
            {key: value for key, value in _ITEM.items() if key != "id"},
            _ITEM | {"id": "not-a-uuid"},
            _ITEM | {"name": ""},
            _ITEM | {"host": ""},
            _ITEM | {"base_path": ""},
            _ITEM | {"subpath": "x"},
        ],
        ids=["missing-id", "invalid-id", "empty-name", "empty-host", "empty-base-path", "unknown"],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            VFSStorageSeed.model_validate(item)


class TestVFSStorageKind:
    def test_the_files_are_planned_whole(self, vfs_storage_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([vfs_storage_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "vfs_storage"
        assert [item.key() for item in batch.items()] == [
            "0198a5a0-0000-7000-8000-00000000b001",
            "0198a5a0-0000-7000-8000-00000000b002",
        ]

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _ITEM)
        second = _write(tmp_path / "second.yaml", _ITEM | {"name": "other"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, vfs_storage_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(vfs_storage_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "vfs_storage: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _ITEM | {"name": ""})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
