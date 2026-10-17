"""User seed files are a `user` kind, and `mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.models.keypair.upserters import KeypairUpserter
from ai.backend.manager.models.user.row import UserRole
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner
from ai.backend.manager.seed.types import SeedKind
from ai.backend.manager.seed.user.seed import UserSeed

_USER_ID = "0198a5a0-0000-7000-8000-000000000001"
_DOMAIN_ID = "0198a5a0-0000-7000-8000-000000000002"


def _keypair(access_key: str = "AKIATEST000000000001", **values: Any) -> dict[str, Any]:
    return {
        "access_key": access_key,
        "secret_key": "secret",
        "resource_policy_id": "0198a5a0-0000-7000-8000-0000000b0003",
        **values,
    }


def _user(user_id: str = _USER_ID, **values: Any) -> dict[str, Any]:
    return {
        "id": user_id,
        "domain_id": _DOMAIN_ID,
        "email": "user@example.com",
        "username": "user",
        "password": "password",
        "resource_policy_id": "0198a5a0-0000-7000-8000-0000000b0001",
        **values,
    }


def _write(path: Path, *users: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "user", "version": 1, "items": list(users)}))
    return path


class TestUserSeed:
    def test_an_unstated_status_and_role_are_an_active_user(self) -> None:
        seed = UserSeed.model_validate(_user())
        assert (seed.status, seed.role) == (UserStatus.ACTIVE, UserRole.USER)

    def test_insert_only_columns_are_not_rewritten_by_an_overwrite(self) -> None:
        update = UserSeed.model_validate(_user()).write().upserter.build_update_values()
        assert {"uuid", "domain_id", "domain_name", "password"}.isdisjoint(update)

    def test_no_keypair_is_written_unless_stated(self) -> None:
        write = UserSeed.model_validate(_user()).write()
        assert write.field_upserters == []
        assert write.field_purgers == []

    def test_the_default_keypair_is_written_last(self) -> None:
        seed = UserSeed.model_validate(
            _user(
                keypairs=[
                    _keypair("AKIADEFAULT000000001", is_default=True),
                    _keypair("AKIAOTHER00000000002"),
                ]
            )
        )
        upserters = seed.write().field_upserters
        assert [
            upserter.access_key for upserter in upserters if isinstance(upserter, KeypairUpserter)
        ] == ["AKIAOTHER00000000002", "AKIADEFAULT000000001"]

    def test_insert_only_keypair_columns_are_not_rewritten_by_an_overwrite(self) -> None:
        seed = UserSeed.model_validate(_user(keypairs=[_keypair()]))
        [upserter] = seed.write().field_upserters
        assert {"user", "access_key", "secret_key"}.isdisjoint(upserter.build_update_values())

    @pytest.mark.parametrize(
        "values",
        [
            {"username": "a" * 65},
            {"email": "a" * 65},
            {"description": "a" * 501},
            {"allowed_client_ip": ["not-an-address"]},
            {"keypairs": [_keypair("A" * 21)]},
            {"keypairs": [_keypair(secret_key="bai-enc:1:config:key:a:b:c")]},
            {"keypairs": [_keypair(dotfiles="x")]},
            {"totp_key": "x"},
        ],
        ids=[
            "long-username",
            "long-email",
            "long-description",
            "bad-ip",
            "long-access-key",
            "encrypted-secret",
            "unknown-keypair-column",
            "unknown-column",
        ],
    )
    def test_a_value_the_columns_refuse_is_refused(self, values: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            UserSeed.model_validate(_user(**values))


class TestUserKind:
    def test_the_user_files_are_planned_after_their_domain_and_policies(
        self, user_seed_dir: Path
    ) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([user_seed_dir])
        assert plan.rejections == []
        names = [batch.kind.name for batch in plan.batches]
        assert names.index(SeedKind.DOMAIN) < names.index(SeedKind.USER)
        assert names.index(SeedKind.USER_RESOURCE_POLICY) < names.index(SeedKind.USER)
        assert names.index(SeedKind.KEYPAIR_RESOURCE_POLICY) < names.index(SeedKind.USER)

    def test_an_access_key_stated_twice_rejects_every_file_stating_it(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _user(keypairs=[_keypair()]))
        second = _write(
            tmp_path / "second.yaml",
            _user(
                "0198a5a0-0000-7000-8000-000000000003",
                email="other@example.com",
                username="other",
                keypairs=[_keypair()],
            ),
        )
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []

    def test_an_access_key_stated_twice_in_one_user_rejects_its_file(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "user.yaml", _user(keypairs=[_keypair(), _keypair()]))
        plan = SeedPlanner(create_seed_kind_registry()).plan([path])
        assert [rejection.source for rejection in plan.rejections] == [str(path)]


class TestCheckCommand:
    def test_the_user_files_pass(self, user_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(user_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "user: 2 files, 2 items" in result.output

    def test_a_bad_address_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _user(allowed_client_ip=["300.0.0.1"]))
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0


class TestUserSeedCheck:
    def test_an_item_keeping_the_rules_passes(self) -> None:
        assert UserSeed.model_validate(_user(keypairs=[_keypair(is_default=True)])).check() == []

    @pytest.mark.parametrize(
        "item",
        [
            _user(container_uid=-1),
            _user(container_main_gid=-1),
            _user(container_gids=[1000, -1]),
            _user(keypairs=[_keypair(is_default=True, is_active=False)]),
        ],
        ids=[
            "negative-uid",
            "negative-main-gid",
            "negative-gid",
            "inactive-default-keypair",
        ],
    )
    def test_an_item_breaking_a_rule_fails(self, item: dict[str, Any]) -> None:
        assert len(UserSeed.model_validate(item).check()) == 1
