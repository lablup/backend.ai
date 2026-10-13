"""The resource preset files are a `resource_preset` seed, and `mgr seed check` reports
what it skips."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.resource_preset.seed import ResourcePresetSeed
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-000000001001"


class TestResourcePresetSeed:
    def test_the_optional_fields_take_the_column_defaults(self) -> None:
        seed = ResourcePresetSeed.model_validate({
            "id": _ID,
            "name": "small",
            "resource_slots": {"cpu": "1"},
        })
        assert seed.shared_memory is None
        assert seed.resource_group_id is None

    def test_shared_memory_is_written_in_bytes(self) -> None:
        seed = ResourcePresetSeed.model_validate({
            "id": _ID,
            "name": "small",
            "resource_slots": {"cpu": "1"},
            "shared_memory": "64m",
        })
        assert seed.write().upserter.build_insert_values()["shared_memory"] == 64 * 2**20

    def test_an_unknown_field_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            ResourcePresetSeed.model_validate({
                "id": _ID,
                "name": "small",
                "resource_slots": {"cpu": "1"},
                "scaling_group_name": "default",
            })

    @pytest.mark.parametrize("name", ["", "x" * 257])
    def test_a_name_outside_the_column_length_is_refused(self, name: str) -> None:
        with pytest.raises(InvalidSeedDocument):
            ResourcePresetSeed.model_validate({
                "id": _ID,
                "name": name,
                "resource_slots": {"cpu": "1"},
            })

    @pytest.mark.parametrize("shared_memory", ["lots", "1.5", "-1", "inf", "8e"])
    def test_a_shared_memory_the_column_cannot_hold_is_refused(self, shared_memory: str) -> None:
        with pytest.raises(InvalidSeedDocument):
            ResourcePresetSeed.model_validate({
                "id": _ID,
                "name": "small",
                "resource_slots": {"cpu": "1"},
                "shared_memory": shared_memory,
            })


class TestResourcePresetKind:
    def test_the_files_are_planned_whole(self, resource_preset_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([resource_preset_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "resource_preset"
        assert len(batch.items()) == 2


class TestCheckCommand:
    def test_the_files_pass(self, resource_preset_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(resource_preset_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "resource_preset: 2 files, 2 items" in result.output
