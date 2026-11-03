"""Domain admin seed files are a `domain_admin` kind, applied after every entity kind."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.repositories.ops.v2.seed.types import SeedRoleGrantWrite
from ai.backend.manager.seed.domain_admin.seed import DomainAdminSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.types import SeedKind

_DOMAIN_ID = "0198a5a0-0000-7000-8000-000000000001"
_USER_ID = "0198a5a0-0000-7000-8000-000000000002"


def _admin(**values: Any) -> dict[str, Any]:
    return {"domain_id": _DOMAIN_ID, "user_id": _USER_ID, **values}


def _write(path: Path, *admins: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "domain_admin", "version": 1, "items": list(admins)}))
    return path


class TestDomainAdminSeed:
    def test_the_key_joins_the_domain_and_the_user(self) -> None:
        seed = DomainAdminSeed.model_validate(_admin())
        assert seed.key() == f"{_DOMAIN_ID}:{_USER_ID}"

    def test_the_item_grants_the_scope_its_preset_role(self) -> None:
        write = DomainAdminSeed.model_validate(_admin()).write()
        assert write == SeedRoleGrantWrite(
            user_id=UserID(uuid.UUID(_USER_ID)),
            scope=DomainID(uuid.UUID(_DOMAIN_ID)),
            preset_name="domain_admin",
        )

    @pytest.mark.parametrize(
        "values",
        [{"user_id": "admin"}, {"role": "admin"}],
        ids=["not-an-id", "unknown-field"],
    )
    def test_an_item_off_the_model_is_refused(self, values: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            DomainAdminSeed.model_validate(_admin(**values))


class TestDomainAdminKind:
    def test_the_admins_are_planned_after_every_entity_kind(self, tmp_path: Path) -> None:
        _write(tmp_path / "admins.yaml", _admin())
        plan = SeedPlanner(create_seed_kind_registry()).plan([tmp_path])
        assert plan.rejections == []
        names = [batch.kind.name for batch in plan.batches]
        assert names[-1] is SeedKind.DOMAIN_ADMIN

    def test_a_pair_stated_in_two_files_rejects_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _admin())
        second = _write(tmp_path / "second.yaml", _admin())
        plan = SeedPlanner(create_seed_kind_registry()).plan([tmp_path])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_admin_files_pass(self, domain_admin_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(domain_admin_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "domain_admin: 1 files, 1 items" in result.output
