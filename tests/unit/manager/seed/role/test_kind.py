"""Role seed files are a `role` kind, and `mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.models.rbac_models.permission.upserters import RolePermissionUpserter
from ai.backend.manager.models.rbac_models.user_role.upserters import UserRoleUpserter
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.role.seed import RoleSeed
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_ROLE_ID = "0198a5a0-0000-7000-8000-000000000001"
_PROJECT_ID = "0198a5a0-0000-7000-8000-000000000002"
_USER_ID = "0198a5a0-0000-7000-8000-000000000003"


def _role(role_id: str = _ROLE_ID, **values: Any) -> dict[str, Any]:
    return {
        "id": role_id,
        "name": "reader",
        "scope_type": "project",
        "scope_id": _PROJECT_ID,
        **values,
    }


def _write(path: Path, *roles: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "role", "version": 1, "items": list(roles)}))
    return path


class TestRoleSeed:
    def test_an_unstated_role_grants_nothing_to_no_one(self) -> None:
        seed = RoleSeed.model_validate(_role())
        write = seed.write()
        assert (seed.auto_assign, seed.role_preset_id) == (False, None)
        assert write.field_upserters == []
        assert write.field_purgers == []

    def test_operations_are_read_into_one_permission_row_per_bit(self) -> None:
        seed = RoleSeed.model_validate(_role(permissions={"session": ["read", "create"]}))
        assert seed.permissions == {"session": Permission.READ | Permission.CREATE}
        assert {
            (str(upserter.entity_type), upserter.permission)
            for upserter in seed.write().field_upserters
            if isinstance(upserter, RolePermissionUpserter)
        } == {("session", Permission.READ), ("session", Permission.CREATE)}

    def test_each_user_is_granted_the_role(self) -> None:
        seed = RoleSeed.model_validate(_role(users=[_USER_ID]))
        assert [
            str(upserter.user_id)
            for upserter in seed.write().field_upserters
            if isinstance(upserter, UserRoleUpserter)
        ] == [_USER_ID]

    def test_insert_only_columns_are_not_rewritten_by_an_overwrite(self) -> None:
        update = RoleSeed.model_validate(_role()).write().upserter.build_update_values()
        assert {"id", "scope_type", "scope_id", "role_preset_id", "source"}.isdisjoint(update)

    def test_a_grant_is_not_rewritten_by_an_overwrite(self) -> None:
        [upserter] = RoleSeed.model_validate(_role(users=[_USER_ID])).write().field_upserters
        assert upserter.build_update_values() == {}

    @pytest.mark.parametrize(
        "values",
        [
            {"name": ""},
            {"name": "a" * 65},
            {"scope_type": "global"},
            {"scope_type": "vfolder"},
            {"permissions": {"session": ["execute"]}},
            {"permissions": {"session": ["read", "read"]}},
            {"permissions": {"session": "read"}},
            {"users": ["not-a-uuid"]},
            {"source": "system"},
        ],
        ids=[
            "empty-name",
            "long-name",
            "global-scope",
            "not-a-role-scope",
            "unknown-operation",
            "repeated-operation",
            "operations-not-a-list",
            "bad-user-id",
            "unknown-column",
        ],
    )
    def test_a_value_the_columns_refuse_is_refused(self, values: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            RoleSeed.model_validate(_role(**values))


class TestRoleKind:
    def test_the_role_files_are_planned_after_their_scopes_and_users(
        self, role_kind_seed_dir: Path
    ) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([role_kind_seed_dir])
        assert plan.rejections == []
        names = [batch.kind.name for batch in plan.batches]
        assert names.index(SeedKind.DOMAIN) < names.index(SeedKind.ROLE)
        assert names.index(SeedKind.PROJECT) < names.index(SeedKind.ROLE)
        assert names.index(SeedKind.USER) < names.index(SeedKind.ROLE)

    def test_a_permission_on_no_entity_type_rejects_its_file(self, tmp_path: Path) -> None:
        bad = _write(tmp_path / "bad.yaml", _role(permissions={"no_such_entity": ["read"]}))
        good = _write(
            tmp_path / "good.yaml",
            _role("0198a5a0-0000-7000-8000-000000000004", permissions={"session": ["read"]}),
        )
        plan = SeedPlanner(create_seed_kind_registry()).plan([bad, good])
        assert [rejection.source for rejection in plan.rejections] == [str(bad)]


class TestCheckCommand:
    def test_the_role_files_pass(self, role_kind_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(role_kind_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "role: 2 files, 2 items" in result.output

    def test_a_bad_scope_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _role(scope_type="global"))
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
