"""The `storage_namespace` kind reads one item per namespace id, and `mgr seed check`
reports what it skips."""

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
from ai.backend.manager.seed.storage_namespace.seed import StorageNamespaceSeed

_ID = "0198a5a0-0000-7000-8000-00000000c001"
_ITEM: dict[str, Any] = {
    "id": _ID,
    "storage_id": "0198a5a0-0000-7000-8000-00000000b001",
    "namespace": "artifacts",
}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "storage_namespace", "version": 1, "items": list(items)})
    )
    return path


class TestStorageNamespaceSeed:
    def test_the_key_is_the_id(self) -> None:
        assert StorageNamespaceSeed.model_validate(_ITEM).key() == _ID

    @pytest.mark.parametrize(
        "item",
        [
            {key: value for key, value in _ITEM.items() if key != "id"},
            _ITEM | {"id": "not-a-uuid"},
            {key: value for key, value in _ITEM.items() if key != "storage_id"},
            _ITEM | {"storage_id": "minio"},
            _ITEM | {"namespace": ""},
            _ITEM | {"bucket": "x"},
        ],
        ids=[
            "missing-id",
            "invalid-id",
            "missing-storage-id",
            "invalid-storage-id",
            "empty-namespace",
            "unknown",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            StorageNamespaceSeed.model_validate(item)


class TestStorageNamespaceKind:
    def test_the_files_are_planned_whole(self, storage_namespace_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([storage_namespace_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "storage_namespace"
        assert [item.key() for item in batch.items()] == [
            "0198a5a0-0000-7000-8000-00000000c001",
            "0198a5a0-0000-7000-8000-00000000c002",
        ]

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _ITEM)
        second = _write(tmp_path / "second.yaml", _ITEM | {"namespace": "other"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, storage_namespace_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(storage_namespace_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "storage_namespace: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _ITEM | {"namespace": ""})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
