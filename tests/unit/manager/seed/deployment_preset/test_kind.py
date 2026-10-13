"""The deployment preset files are a `deployment_preset` seed, and `mgr seed check` reports
what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.deployment_preset.seed import DeploymentPresetSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_REQUIRED: dict[str, Any] = {
    "id": "0198a5a0-0000-7000-8000-00000000e001",
    "runtime_variant_id": "0198a5a0-0000-7000-8000-00000000e002",
    "name": "custom",
    "image_id": "0198a5a0-0000-7000-8000-00000000e003",
}


class TestDeploymentPresetSeed:
    def test_the_optional_fields_take_the_column_defaults(self) -> None:
        seed = DeploymentPresetSeed.model_validate(_REQUIRED)
        assert seed.resource_slots == {}
        assert seed.cluster_mode == "single-node"
        assert seed.cluster_size == 1
        assert seed.replica_count == 1
        assert seed.deployment_strategy == DeploymentStrategy.ROLLING
        assert seed.deployment_strategy_spec == {}

    def test_an_unknown_field_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            DeploymentPresetSeed.model_validate(_REQUIRED | {"rank": 100})

    @pytest.mark.parametrize("name", ["", "x" * 257])
    def test_a_name_outside_the_column_length_is_refused(self, name: str) -> None:
        with pytest.raises(InvalidSeedDocument):
            DeploymentPresetSeed.model_validate(_REQUIRED | {"name": name})

    def test_a_cluster_mode_over_the_column_length_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            DeploymentPresetSeed.model_validate(_REQUIRED | {"cluster_mode": "x" * 17})

    @pytest.mark.parametrize("field", ["cluster_size", "replica_count", "revision_history_limit"])
    def test_an_integer_over_the_column_range_is_refused(self, field: str) -> None:
        with pytest.raises(InvalidSeedDocument):
            DeploymentPresetSeed.model_validate(_REQUIRED | {field: 2**31})

    @pytest.mark.parametrize(
        "resource_slots",
        [{"x" * 65: 1}, {"cpu": "0.0000001"}, {"mem": 10**18}],
        ids=["slot-name-too-long", "too-many-decimal-places", "too-many-digits"],
    )
    def test_a_slot_the_column_cannot_hold_is_refused(self, resource_slots: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            DeploymentPresetSeed.model_validate(_REQUIRED | {"resource_slots": resource_slots})

    def test_a_model_definition_without_models_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            DeploymentPresetSeed.model_validate(_REQUIRED | {"model_definition": {}})


class TestDeploymentPresetKind:
    def test_the_files_are_planned_whole(self, deployment_preset_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([deployment_preset_seed_dir])
        assert plan.rejections == []
        [batch] = [b for b in plan.batches if b.kind.name == SeedKind.DEPLOYMENT_PRESET]
        assert len(batch.items()) == 2


class TestCheckCommand:
    def test_the_files_pass(self, deployment_preset_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(deployment_preset_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "deployment_preset: 2 files, 2 items" in result.output
