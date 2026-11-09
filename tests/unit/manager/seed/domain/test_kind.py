"""Domain seed files are a `domain` kind, and `mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.types import ResourceSlot, VFolderHostPermission
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.models.domain.upserters import DomainUpserter
from ai.backend.manager.seed.domain.seed import DomainSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner


def _domain(name: str, domain_id: str, **values: Any) -> dict[str, Any]:
    return {"id": domain_id, "name": name, **values}


def _write(path: Path, *domains: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "domain", "version": 1, "items": list(domains)}))
    return path


class TestDomainSeed:
    def test_an_unstated_column_takes_the_creation_default(self) -> None:
        seed = DomainSeed.model_validate(_domain("lab", "0198a5a0-0000-7000-8000-000000000001"))
        upserter = seed.write().upserter
        assert isinstance(upserter, DomainUpserter)
        assert upserter.build_insert_values() == {
            "id": seed.id,
            "name": "lab",
            "description": None,
            "is_active": True,
            "is_default": False,
            "total_resource_slots": ResourceSlot(),
            "allowed_vfolder_hosts": {},
            "allowed_docker_registries": [],
        }

    def test_the_name_is_not_rewritten_by_an_overwrite(self) -> None:
        seed = DomainSeed.model_validate(_domain("lab", "0198a5a0-0000-7000-8000-000000000001"))
        assert "name" not in seed.write().upserter.build_update_values()

    def test_the_vfolder_host_permissions_are_read_by_value(self) -> None:
        seed = DomainSeed.model_validate(
            _domain(
                "lab",
                "0198a5a0-0000-7000-8000-000000000001",
                allowed_vfolder_hosts={"local:volume1": ["create-vfolder"]},
            )
        )
        assert seed.allowed_vfolder_hosts == {"local:volume1": [VFolderHostPermission.CREATE]}

    def test_an_unknown_vfolder_host_permission_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            DomainSeed.model_validate(
                _domain(
                    "lab",
                    "0198a5a0-0000-7000-8000-000000000001",
                    allowed_vfolder_hosts={"local:volume1": ["fly"]},
                )
            )

    def test_an_unknown_column_is_refused(self) -> None:
        with pytest.raises(InvalidSeedDocument):
            DomainSeed.model_validate(
                _domain("lab", "0198a5a0-0000-7000-8000-000000000001", dotfiles="x")
            )

    def test_no_field_row_is_written(self) -> None:
        write = DomainSeed.model_validate(
            _domain("lab", "0198a5a0-0000-7000-8000-000000000001")
        ).write()
        assert write.field_upserters == []
        assert write.field_purgers == []


class TestDomainKind:
    def test_the_domain_files_are_planned_whole(self, domain_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([domain_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "domain"
        assert len(batch.items()) == 2


class TestCheckCommand:
    def test_the_domain_files_pass(self, domain_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(domain_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "domain: 2 files, 2 items" in result.output

    @pytest.mark.parametrize("name", ["", "a" * 65, "two words"], ids=["empty", "65", "not-slug"])
    def test_a_name_the_column_refuses_fails_the_command(self, tmp_path: Path, name: str) -> None:
        path = _write(tmp_path / "bad.yaml", _domain(name, "0198a5a0-0000-7000-8000-000000000001"))
        plan = SeedPlanner(create_seed_kind_registry()).plan([path])
        assert [rejection.source for rejection in plan.rejections] == [str(path)]
        assert plan.batches == []
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
