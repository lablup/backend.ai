"""The resource policy files are read per kind, and `mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot, VFolderHostPermission
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.models.resource_policy.upserters import KeyPairResourcePolicyUpserter
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.resource_policy.seed import KeyPairResourcePolicySeed
from ai.backend.manager.seed.runner import SeedPlanner


def _keypair_policy(uuid: str, name: str, **values: Any) -> dict[str, Any]:
    return {
        "uuid": uuid,
        "name": name,
        "total_resource_slots": {"cpu": "1"},
        "max_concurrent_sessions": 1,
        "max_containers_per_session": 1,
        "idle_timeout": 0,
        **values,
    }


def _write(path: Path, kind: str, *items: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": kind, "version": 1, "items": list(items)}))
    return path


# One valid item per kind, without its uuid.
_ITEMS: list[tuple[str, dict[str, Any]]] = [
    (
        "user_resource_policy",
        {
            "name": "shared",
            "max_vfolder_count": 0,
            "max_quota_scope_size": -1,
            "max_session_count_per_model_session": 1,
        },
    ),
    (
        "project_resource_policy",
        {
            "name": "shared",
            "max_vfolder_count": 0,
            "max_quota_scope_size": -1,
            "max_network_count": 1,
        },
    ),
    ("keypair_resource_policy", _keypair_policy("", "shared")),
]


class TestKeyPairResourcePolicySeed:
    def test_an_unstated_column_takes_the_row_default(self) -> None:
        seed = KeyPairResourcePolicySeed.model_validate(
            _keypair_policy("0198a5a0-0000-7000-8000-000000000001", "minimal")
        )
        upserter = seed.write().upserter
        assert isinstance(upserter, KeyPairResourcePolicyUpserter)
        assert upserter.is_default is False
        assert upserter.default_for_unspecified == DefaultForUnspecified.LIMITED
        assert upserter.max_session_lifetime == 0
        assert upserter.max_pending_session_count is None
        assert upserter.max_pending_session_resource_slots is None
        assert upserter.max_priority is None
        assert upserter.max_concurrent_sftp_sessions == 1
        assert upserter.allowed_vfolder_hosts == {}

    def test_the_stated_values_reach_the_upserter(self) -> None:
        seed = KeyPairResourcePolicySeed.model_validate(
            _keypair_policy(
                "0198a5a0-0000-7000-8000-000000000001",
                "full",
                max_pending_session_resource_slots={"cpu": "2"},
                allowed_vfolder_hosts={"local": ["mount-in-session", "create-vfolder"]},
            )
        )
        upserter = seed.write().upserter
        assert isinstance(upserter, KeyPairResourcePolicyUpserter)
        assert upserter.total_resource_slots == ResourceSlot({"cpu": 1})
        assert upserter.max_pending_session_resource_slots == ResourceSlot({"cpu": 2})
        assert upserter.allowed_vfolder_hosts == {
            "local": [VFolderHostPermission.CREATE, VFolderHostPermission.MOUNT_IN_SESSION]
        }

    def test_an_unknown_vfolder_host_permission_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            KeyPairResourcePolicySeed.model_validate(
                _keypair_policy(
                    "0198a5a0-0000-7000-8000-000000000001",
                    "bad",
                    allowed_vfolder_hosts={"local": ["fly"]},
                )
            )

    def test_an_unknown_field_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            KeyPairResourcePolicySeed.model_validate(
                _keypair_policy("0198a5a0-0000-7000-8000-000000000001", "bad", extra=1)
            )


class TestResourcePolicyKinds:
    def test_the_files_are_planned_in_kind_order(self, resource_policy_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([resource_policy_seed_dir])
        assert plan.rejections == []
        assert [batch.kind.name for batch in plan.batches] == [
            "user_resource_policy",
            "project_resource_policy",
            "keypair_resource_policy",
        ]

    @pytest.mark.parametrize(("kind", "item"), _ITEMS, ids=[kind for kind, _ in _ITEMS])
    @pytest.mark.parametrize("name", ["", "x" * 257], ids=["empty", "beyond-the-column"])
    def test_a_name_the_column_cannot_hold_skips_the_file(
        self, tmp_path: Path, kind: str, item: dict[str, Any], name: str
    ) -> None:
        path = _write(
            tmp_path / "policy.yaml",
            kind,
            item | {"uuid": "0198a5a0-0000-7000-8000-000000000001", "name": name},
        )
        plan = SeedPlanner(create_seed_kind_registry()).plan([path])
        [rejection] = plan.rejections
        assert rejection.source == str(path)
        assert "name" in rejection.reason
        assert plan.batches == []


class TestCheckCommand:
    def test_the_resource_policy_files_pass(self, resource_policy_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(resource_policy_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "user_resource_policy: 1 files, 1 items" in result.output
        assert "project_resource_policy: 1 files, 1 items" in result.output
        assert "keypair_resource_policy: 1 files, 1 items" in result.output
