"""The `idle_checker_assignment` kind reads one item per checker and scope, and writes it
with the creator the assignment API uses."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.models.idle_checker.creators import IdleCheckerAssignmentCreator
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.idle_checker_assignment.seed import IdleCheckerAssignmentSeed
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_CHECKER = "0198a5a0-0000-7000-8000-00000000f001"
_SCOPE = "0198a5a0-0000-7000-8000-00000000d001"
_ITEM: dict[str, Any] = {"idle_checker_id": _CHECKER, "scope_type": "domain", "scope_id": _SCOPE}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "idle_checker_assignment", "version": 1, "items": list(items)})
    )
    return path


class TestIdleCheckerAssignmentSeed:
    def test_the_key_joins_the_scope_and_the_checker(self) -> None:
        seed = IdleCheckerAssignmentSeed.model_validate(_ITEM)
        assert seed.key() == f"domain:{_SCOPE}:{_CHECKER}"

    def test_enabled_defaults_to_true(self) -> None:
        seed = IdleCheckerAssignmentSeed.model_validate(_ITEM)
        assert seed.enabled is True

    @pytest.mark.parametrize("enabled", [True, False])
    def test_the_creator_carries_enabled(self, enabled: bool) -> None:
        write = IdleCheckerAssignmentSeed.model_validate(_ITEM | {"enabled": enabled}).write()
        assert write.creator == IdleCheckerAssignmentCreator(enabled=enabled)
        assert str(write.target) == _CHECKER

    @pytest.mark.parametrize(
        ("scope_type", "entity_type"),
        [
            ("domain", DomainEntityType()),
            ("project", ProjectEntityType()),
            ("resource_group", ResourceGroupEntityType()),
            ("user", UserEntityType()),
        ],
    )
    def test_the_scope_is_the_entity_its_type_names(
        self, scope_type: str, entity_type: EntityType
    ) -> None:
        write = IdleCheckerAssignmentSeed.model_validate(_ITEM | {"scope_type": scope_type}).write()
        assert write.scope.entity_type() == entity_type
        assert str(write.scope) == _SCOPE

    @pytest.mark.parametrize(
        "change",
        [
            {"idle_checker_id": None},
            {"scope_type": None},
            {"scope_id": None},
            {"scope_type": "keypair"},
            {"scope_id": "not-a-uuid"},
            {"id": _CHECKER},
        ],
        ids=[
            "missing-checker",
            "missing-scope-type",
            "missing-scope-id",
            "unknown-scope-type",
            "invalid-scope-id",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, change: dict[str, Any]) -> None:
        item = {key: value for key, value in (_ITEM | change).items() if value is not None}
        with pytest.raises(InvalidSeedDocument):
            IdleCheckerAssignmentSeed.model_validate(item)


class TestIdleCheckerAssignmentKind:
    def test_the_kind_is_applied_after_the_entity_kinds(self) -> None:
        kinds = [kind.name for kind in create_seed_kind_registry().ordered()]
        assert kinds.index(SeedKind.IDLE_CHECKER_ASSIGNMENT) > kinds.index(SeedKind.IDLE_CHECKER)
        assert kinds.index(SeedKind.IDLE_CHECKER_ASSIGNMENT) > kinds.index(SeedKind.RESOURCE_GROUP)

    def test_the_files_are_planned_whole(self, tmp_path: Path) -> None:
        other = _ITEM | {"scope_type": "user"}
        path = _write(tmp_path / "assignments.yaml", _ITEM, other)
        plan = SeedPlanner(create_seed_kind_registry()).plan([path])
        assert plan.rejections == []
        [batch] = plan.batches
        assert [item.key() for item in batch.items()] == [
            f"domain:{_SCOPE}:{_CHECKER}",
            f"user:{_SCOPE}:{_CHECKER}",
        ]

    def test_a_pair_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _ITEM)
        second = _write(tmp_path / "second.yaml", _ITEM | {"enabled": False})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_file_passes(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "assignments.yaml", _ITEM)
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code == 0, result.output
        assert "idle_checker_assignment: 1 files, 1 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _ITEM | {"scope_type": "keypair"})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
