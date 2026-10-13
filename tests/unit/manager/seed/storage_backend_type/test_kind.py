"""The `storage_backend_type` kind reads one item per backend name, and `mgr seed check`
reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.data.storage.types import StorageBackendCapability
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.storage_backend_type.seed import StorageBackendTypeSeed


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "storage_backend_type", "version": 1, "items": list(items)})
    )
    return path


class TestStorageBackendTypeSeed:
    def test_the_key_is_the_name(self) -> None:
        seed = StorageBackendTypeSeed.model_validate({"name": "vfs", "capabilities": ["quota"]})
        assert seed.key() == "vfs"
        assert seed.capabilities == frozenset({StorageBackendCapability.QUOTA})

    @pytest.mark.parametrize(
        "item",
        [
            {"capabilities": []},
            {"name": "vfs"},
            {"name": "", "capabilities": []},
            {"name": "x" * 65, "capabilities": []},
            {"name": "vfs", "capabilities": ["teleport"]},
            {"name": "vfs", "capabilities": [], "id": "0198a5a0-0000-7000-8000-000000000001"},
        ],
        ids=[
            "missing-name",
            "missing-capabilities",
            "empty",
            "too-long",
            "unknown-capability",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            StorageBackendTypeSeed.model_validate(item)


class TestStorageBackendTypeKind:
    def test_the_files_are_planned_whole(self, storage_backend_type_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([storage_backend_type_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "storage_backend_type"
        assert [item.key() for item in batch.items()] == ["vfs", "noop"]

    def test_a_name_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", {"name": "vfs", "capabilities": []})
        second = _write(tmp_path / "second.yaml", {"name": "vfs", "capabilities": []})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, storage_backend_type_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(storage_backend_type_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "storage_backend_type: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", {"name": "", "capabilities": []})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
