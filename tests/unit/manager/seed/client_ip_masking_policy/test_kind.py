"""The `client_ip_masking_policy` kind reads one item per target, and `mgr seed check`
reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.client_ip_masking_policy.seed import ClientIPMaskingPolicySeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "client_ip_masking_policy", "version": 1, "items": list(items)})
    )
    return path


class TestClientIPMaskingPolicySeed:
    def test_the_key_is_the_target_type(self) -> None:
        seed = ClientIPMaskingPolicySeed.model_validate({
            "target_type": "login_history",
            "mode": "none",
        })
        assert seed.key() == "login_history"

    @pytest.mark.parametrize(
        "prefix", [{"ipv4_prefix": 0}, {"ipv4_prefix": 32}, {"ipv6_prefix": 128}]
    )
    def test_a_prefix_within_the_width_is_accepted(self, prefix: dict[str, int]) -> None:
        ClientIPMaskingPolicySeed.model_validate({
            "target_type": "default",
            "mode": "truncate",
            **prefix,
        })

    @pytest.mark.parametrize(
        "item",
        [
            {"mode": "drop"},
            {"target_type": "default"},
            {"target_type": "sessions", "mode": "drop"},
            {"target_type": "default", "mode": "hash"},
            {"target_type": "default", "mode": "truncate", "ipv4_prefix": 33},
            {"target_type": "default", "mode": "truncate", "ipv4_prefix": -1},
            {"target_type": "default", "mode": "truncate", "ipv6_prefix": 129},
            {
                "target_type": "default",
                "mode": "drop",
                "id": "0198a5a0-0000-7000-8000-000000000001",
            },
        ],
        ids=[
            "missing-target",
            "missing-mode",
            "unknown-target",
            "unknown-mode",
            "ipv4-too-wide",
            "ipv4-negative",
            "ipv6-too-wide",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            ClientIPMaskingPolicySeed.model_validate(item)


class TestClientIPMaskingPolicyKind:
    def test_the_files_are_planned_whole(self, client_ip_masking_policy_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([client_ip_masking_policy_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "client_ip_masking_policy"
        assert [item.key() for item in batch.items()] == ["default", "audit_logs"]

    def test_a_target_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", {"target_type": "default", "mode": "drop"})
        second = _write(tmp_path / "second.yaml", {"target_type": "default", "mode": "none"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, client_ip_masking_policy_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(client_ip_masking_policy_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "client_ip_masking_policy: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path / "bad.yaml", {"target_type": "default", "mode": "truncate", "ipv4_prefix": 33}
        )
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
