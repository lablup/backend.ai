"""The runtime variant preset files are a `runtime_variant_preset` seed, and
`mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.runtime_variant_preset.seed import RuntimeVariantPresetSeed

_REQUIRED: dict[str, Any] = {
    "id": "0198a5a0-0000-7000-8000-00000000e001",
    "runtime_variant_id": "0198a5a0-0000-7000-8000-00000000c001",
    "name": "max-num-seqs",
    "rank": 100,
    "preset_target": "env",
    "value_type": "int",
    "key": "MAX_NUM_SEQS",
}


class TestRuntimeVariantPresetSeed:
    def test_the_optional_fields_take_the_column_defaults(self) -> None:
        seed = RuntimeVariantPresetSeed.model_validate(_REQUIRED)
        assert seed.preset_key == "MAX_NUM_SEQS"
        assert seed.required is False
        assert seed.description is None
        assert seed.default_value is None
        assert seed.added_version is None
        assert seed.ui_option is None

    def test_an_unknown_field_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            RuntimeVariantPresetSeed.model_validate({**_REQUIRED, "ui_type": "slider"})

    @pytest.mark.parametrize(
        "field",
        [
            pytest.param({"name": ""}, id="empty-name"),
            pytest.param({"name": "x" * 257}, id="long-name"),
            pytest.param({"key": "x" * 257}, id="long-key"),
            pytest.param({"default_value": "1" * 513}, id="long-default-value"),
            pytest.param({"category": "x" * 65}, id="long-category"),
            pytest.param({"display_name": "x" * 257}, id="long-display-name"),
            pytest.param({"rank": -1}, id="negative-rank"),
            pytest.param({"added_version": "0.9.0rc1"}, id="prerelease-version"),
            pytest.param({"preset_target": "file"}, id="unknown-target"),
        ],
    )
    def test_a_value_the_column_does_not_take_is_refused(self, field: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            RuntimeVariantPresetSeed.model_validate({**_REQUIRED, **field})

    def test_a_flag_outside_args_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            RuntimeVariantPresetSeed.model_validate({
                **_REQUIRED,
                "preset_target": "env",
                "value_type": "flag",
            })

    def test_a_default_value_of_another_type_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            RuntimeVariantPresetSeed.model_validate({**_REQUIRED, "default_value": "many"})

    def test_a_ui_option_without_its_config_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            RuntimeVariantPresetSeed.model_validate({
                **_REQUIRED,
                "ui_option": {"ui_type": "slider"},
            })


class TestRuntimeVariantPresetKind:
    def test_the_files_are_planned_whole(self, runtime_variant_preset_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([runtime_variant_preset_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "runtime_variant_preset"
        assert len(batch.items()) == 2


class TestCheckCommand:
    def test_the_files_pass(self, runtime_variant_preset_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(runtime_variant_preset_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "runtime_variant_preset: 1 files, 2 items" in result.output
