"""Project seed files are a `project` kind, and `mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.project.seed import ProjectSeed
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_PROJECT_ID = "0198a5a0-0000-7000-8000-000000000001"
_DOMAIN_ID = "0198a5a0-0000-7000-8000-000000000002"


def _project(name: str = "lab", **values: Any) -> dict[str, Any]:
    return {
        "id": _PROJECT_ID,
        "domain_id": _DOMAIN_ID,
        "name": name,
        "resource_policy": "default",
        **values,
    }


def _write(path: Path, *projects: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "project", "version": 1, "items": list(projects)}))
    return path


class TestProjectSeed:
    def test_an_unstated_type_is_general(self) -> None:
        assert ProjectSeed.model_validate(_project()).type is ProjectType.GENERAL

    def test_the_type_is_read_by_value(self) -> None:
        seed = ProjectSeed.model_validate(_project(type="model-store"))
        assert seed.type is ProjectType.MODEL_STORE

    def test_insert_only_columns_are_not_rewritten_by_an_overwrite(self) -> None:
        seed = ProjectSeed.model_validate(_project())
        update = seed.write().upserter.build_update_values()
        assert {"domain_name", "type", "creator_id"}.isdisjoint(update)

    def test_only_the_project_row_is_written(self) -> None:
        write = ProjectSeed.model_validate(_project()).write()
        assert write.field_upserters == []
        assert write.field_purgers == []

    def test_a_description_longer_than_the_column_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            ProjectSeed.model_validate(_project(description="a" * 513))

    def test_an_unknown_column_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            ProjectSeed.model_validate(_project(dotfiles="x"))


class TestProjectKind:
    def test_the_project_files_are_planned_after_their_domain(self, project_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([project_seed_dir])
        assert plan.rejections == []
        names = [batch.kind.name for batch in plan.batches]
        assert names.index(SeedKind.DOMAIN) < names.index(SeedKind.PROJECT)
        assert names.index(SeedKind.PROJECT_RESOURCE_POLICY) < names.index(SeedKind.PROJECT)


class TestCheckCommand:
    def test_the_project_files_pass(self, project_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(project_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "project: 2 files, 2 items" in result.output

    @pytest.mark.parametrize("name", ["", "a" * 65, "two words"], ids=["empty", "65", "not-slug"])
    def test_a_name_the_column_refuses_fails_the_command(self, tmp_path: Path, name: str) -> None:
        path = _write(tmp_path / "bad.yaml", _project(name))
        plan = SeedPlanner(create_seed_kind_registry()).plan([path])
        assert [rejection.source for rejection in plan.rejections] == [str(path)]
        assert plan.batches == []
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
