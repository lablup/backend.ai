"""The role files are a `role_preset` seed, and `mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.seed.registry import SeedKindRegistry
from ai.backend.manager.seed.role_preset.kinds import PermissionKinds
from ai.backend.manager.seed.runner import SeedPlanner


def _role(name: str, preset_id: str, granted: dict[str, list[str]]) -> dict[str, Any]:
    permissions: dict[str, list[str]] = {kind: [] for kind in PermissionKinds().declared()}
    permissions.update(granted)
    return {
        "id": preset_id,
        "name": name,
        "scope_type": "project",
        "auto_assign": False,
        "permissions": permissions,
    }


def _write(path: Path, *roles: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "role_preset", "version": 1, "items": list(roles)}))
    return path


class TestRolePresetKind:
    def test_the_role_files_are_planned_whole(self, role_seed_dir: Path) -> None:
        plan = SeedPlanner(SeedKindRegistry.default()).plan([role_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name() == "role_preset"
        assert len(batch.items()) == 3

    def test_a_member_beyond_its_admin_skips_the_member_file(self, tmp_path: Path) -> None:
        admin = _write(
            tmp_path / "admin.yaml",
            _role("team_admin", "0198a5a0-0000-7000-8000-000000000001", {"project": ["read"]}),
        )
        member = _write(
            tmp_path / "member.yaml",
            _role(
                "team_member",
                "0198a5a0-0000-7000-8000-000000000002",
                {"project": ["read", "update"]},
            ),
        )
        plan = SeedPlanner(SeedKindRegistry.default()).plan([admin, member])
        assert [rejection.source for rejection in plan.rejections] == [str(member)]
        [batch] = plan.batches
        assert [file.source for file in batch.files] == [str(admin)]

    def test_a_missing_entity_type_skips_the_file(self, tmp_path: Path) -> None:
        role = _role("lonely", "0198a5a0-0000-7000-8000-000000000003", {})
        del role["permissions"]["project"]
        path = _write(tmp_path / "lonely.yaml", role)
        plan = SeedPlanner(SeedKindRegistry.default()).plan([path])
        assert [rejection.source for rejection in plan.rejections] == [str(path)]
        assert "project is not stated" in plan.rejections[0].reason


class TestCheckCommand:
    def test_the_role_files_pass(self, role_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(role_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "role_preset: 3 files, 3 items" in result.output

    def test_a_skipped_file_fails_the_command(self, tmp_path: Path, role_seed_dir: Path) -> None:
        unknown = tmp_path / "unknown.yaml"
        unknown.write_text(yaml.safe_dump({"kind": "omega", "version": 1, "items": []}))
        result = CliRunner().invoke(cli, ["check", str(role_seed_dir), str(unknown)])
        assert result.exit_code != 0
        assert "role_preset: 3 files, 3 items" in result.output
