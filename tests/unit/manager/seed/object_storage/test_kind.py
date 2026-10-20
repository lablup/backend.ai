"""The `object_storage` kind reads one item per storage, and `mgr seed check` reports what
it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.object_storage.seed import ObjectStorageSeed
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-00000000b001"
_ITEM: dict[str, Any] = {
    "id": _ID,
    "name": "minio",
    "host": "storage-proxy",
    "access_key": "minioadmin",
    "secret_key": "minioadmin",
    "endpoint": "http://127.0.0.1:9000",
}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "object_storage", "version": 1, "items": list(items)}))
    return path


class TestObjectStorageSeed:
    def test_the_key_is_the_id(self) -> None:
        seed = ObjectStorageSeed.model_validate(_ITEM)
        assert seed.key() == _ID

    def test_the_region_may_be_left_out(self) -> None:
        seed = ObjectStorageSeed.model_validate(_ITEM)
        assert seed.region is None

    @pytest.mark.parametrize(
        "item",
        [
            {key: value for key, value in _ITEM.items() if key != "id"},
            {key: value for key, value in _ITEM.items() if key != "secret_key"},
            _ITEM | {"id": "minio"},
            _ITEM | {"name": ""},
            _ITEM | {"host": ""},
            _ITEM | {"endpoint": ""},
            _ITEM | {"bucket": "models"},
        ],
        ids=[
            "missing-id",
            "missing-secret-key",
            "bad-id",
            "empty-name",
            "empty-host",
            "empty-endpoint",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            ObjectStorageSeed.model_validate(item)


class TestObjectStorageKind:
    def test_the_files_are_planned_whole(self, object_storage_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([object_storage_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "object_storage"
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
    def test_the_files_pass(self, object_storage_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(object_storage_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "object_storage: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _ITEM | {"name": ""})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0


class TestObjectStorageSeedCheck:
    def test_an_item_keeping_the_rules_passes(self) -> None:
        assert ObjectStorageSeed.model_validate(_ITEM).check() == []

    @pytest.mark.parametrize(
        "item",
        [
            {**_ITEM, "name": "  "},
            {**_ITEM, "name": "x" * 257},
        ],
        ids=[
            "blank-name",
            "too-long-name",
        ],
    )
    def test_an_item_breaking_a_rule_fails(self, item: dict[str, Any]) -> None:
        assert len(ObjectStorageSeed.model_validate(item).check()) == 1
