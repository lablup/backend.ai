"""Project member seed files are a `project_member` kind, applied after every entity kind."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.repositories.ops.v2.seed.types import SeedRosterWrite
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.project_member.seed import ProjectMemberSeed
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_PROJECT_ID = "0198a5a0-0000-7000-8000-000000000001"
_USER_ID = "0198a5a0-0000-7000-8000-000000000002"


def _member(**values: Any) -> dict[str, Any]:
    return {"project_id": _PROJECT_ID, "user_id": _USER_ID, **values}


def _write(path: Path, *members: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "project_member", "version": 1, "items": list(members)})
    )
    return path


class TestProjectMemberSeed:
    def test_the_key_joins_the_project_and_the_user(self) -> None:
        seed = ProjectMemberSeed.model_validate(_member())
        assert seed.key() == f"{_PROJECT_ID}:{_USER_ID}"

    def test_the_item_is_written_onto_the_roster(self) -> None:
        write = ProjectMemberSeed.model_validate(_member()).write()
        assert write == SeedRosterWrite(
            project_id=ProjectID(uuid.UUID(_PROJECT_ID)), user_id=UserID(uuid.UUID(_USER_ID))
        )

    @pytest.mark.parametrize(
        "values",
        [{"user_id": "member"}, {"role": "admin"}],
        ids=["not-an-id", "unknown-field"],
    )
    def test_an_item_off_the_model_is_refused(self, values: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            ProjectMemberSeed.model_validate(_member(**values))


class TestProjectMemberKind:
    def test_the_members_are_planned_after_every_entity_kind(
        self, project_member_seed_dir: Path
    ) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([project_member_seed_dir])
        assert plan.rejections == []
        names = [batch.kind.name for batch in plan.batches]
        assert names[-1] is SeedKind.PROJECT_MEMBER

    def test_a_pair_stated_in_two_files_rejects_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _member())
        second = _write(tmp_path / "second.yaml", _member())
        plan = SeedPlanner(create_seed_kind_registry()).plan([tmp_path])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_member_files_pass(self, project_member_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(project_member_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "project_member: 1 files, 2 items" in result.output
