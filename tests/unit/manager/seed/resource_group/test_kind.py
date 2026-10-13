"""Resource group seed files are a `resource_group` kind, and `mgr seed check` reports what
it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.models.resource_group.types import ResourceGroupOpts
from ai.backend.manager.models.resource_group.upserters import ResourceGroupUpserter
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.resource_group.seed import ResourceGroupSeed
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-000000000001"


def _group(name: str = "lab", **values: Any) -> dict[str, Any]:
    return {"id": _ID, "name": name, "driver": "static", "scheduler": "fifo", **values}


def _write(path: Path, *groups: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "resource_group", "version": 1, "items": list(groups)}))
    return path


class TestResourceGroupSeed:
    def test_an_unstated_column_takes_the_creation_default(self) -> None:
        seed = ResourceGroupSeed.model_validate(_group())
        upserter = seed.write().upserter
        assert isinstance(upserter, ResourceGroupUpserter)
        assert upserter.build_insert_values() == {
            "id": seed.id,
            "name": "lab",
            "description": None,
            "is_active": True,
            "is_public": True,
            "is_default": False,
            "wsproxy_addr": None,
            "wsproxy_api_token": None,
            "driver": "static",
            "driver_opts": {},
            "scheduler": "fifo",
            "scheduler_opts": ResourceGroupOpts(),
            "use_host_network": False,
        }

    def test_the_name_is_not_rewritten_by_an_overwrite(self) -> None:
        seed = ResourceGroupSeed.model_validate(_group())
        assert "name" not in seed.write().upserter.build_update_values()

    def test_no_field_row_is_written(self) -> None:
        write = ResourceGroupSeed.model_validate(_group()).write()
        assert write.field_upserters == []
        assert write.field_purgers == []

    def test_an_unknown_column_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            ResourceGroupSeed.model_validate(_group(fair_share_spec={}))

    def test_an_unknown_scheduler_option_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            ResourceGroupSeed.model_validate(
                _group(scheduler_opts={"agent_selection_strategy": "nowhere"})
            )


class TestResourceGroupKind:
    def test_the_resource_group_file_is_planned_whole(self, resource_group_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([resource_group_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "resource_group"
        assert len(batch.items()) == 2


class TestCheckCommand:
    def test_the_resource_group_file_passes(self, resource_group_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(resource_group_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "resource_group: 1 files, 2 items" in result.output

    @pytest.mark.parametrize(
        "values",
        [
            {"name": ""},
            {"name": "a" * 65},
            {"description": "a" * 513},
            {"wsproxy_addr": "a" * 1025},
            {"wsproxy_api_token": "a" * 129},
            {"driver": "a" * 65},
            {"scheduler": "a" * 65},
        ],
        ids=["empty-name", "name", "description", "wsproxy_addr", "token", "driver", "scheduler"],
    )
    def test_a_value_the_column_refuses_fails_the_command(
        self, tmp_path: Path, values: dict[str, Any]
    ) -> None:
        path = _write(tmp_path / "bad.yaml", _group() | values)
        plan = SeedPlanner(create_seed_kind_registry()).plan([path])
        assert [rejection.source for rejection in plan.rejections] == [str(path)]
        assert plan.batches == []
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
