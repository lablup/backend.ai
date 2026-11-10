"""The runtime variant files are a `runtime_variant` seed, and `mgr seed check` reports
what it skips."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.runtime_variant.seed import RuntimeVariantSeed


class TestRuntimeVariantSeed:
    def test_the_optional_fields_take_the_column_defaults(self) -> None:
        seed = RuntimeVariantSeed.model_validate({
            "id": "0198a5a0-0000-7000-8000-00000000c001",
            "name": "custom",
        })
        assert seed.description is None
        assert seed.reads_vfolder_config_files is False
        assert seed.default_model_definition == DefaultModelDefinition()

    def test_an_unknown_field_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            RuntimeVariantSeed.model_validate({
                "id": "0198a5a0-0000-7000-8000-00000000c001",
                "name": "custom",
                "port": 8000,
            })

    def test_a_model_without_a_port_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            RuntimeVariantSeed.model_validate({
                "id": "0198a5a0-0000-7000-8000-00000000c001",
                "name": "custom",
                "default_model_definition": {"models": [{"name": "m", "service": {}}]},
            })

    @pytest.mark.parametrize("name", ["", "x" * 129])
    def test_a_name_outside_the_column_length_is_refused(self, name: str) -> None:
        with pytest.raises(InvalidSeedDocument):
            RuntimeVariantSeed.model_validate({
                "id": "0198a5a0-0000-7000-8000-00000000c001",
                "name": name,
            })


class TestRuntimeVariantKind:
    def test_the_files_are_planned_whole(self, runtime_variant_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([runtime_variant_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "runtime_variant"
        assert len(batch.items()) == 2


class TestCheckCommand:
    def test_the_files_pass(self, runtime_variant_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(runtime_variant_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "runtime_variant: 2 files, 2 items" in result.output
