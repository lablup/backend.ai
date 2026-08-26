from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai.backend.install.context import Context

from .conftest import InstallerHarness


def _load(filename: str) -> dict[str, Any]:
    with Context.resource_path("ai.backend.install.fixtures", filename) as path:
        data: dict[str, Any] = json.loads(Path(path).read_bytes())
        return data


class TestLoadFixtures:
    async def test_every_populated_fixture_is_readable(self, harness: InstallerHarness) -> None:
        """`load_fixtures` hands paths to the manager CLI without opening them,
        so a fixture gone missing or malformed only surfaces at install time.
        """
        await harness.load_fixtures()

        populated = [
            Path(argv[-1])
            for argv in harness.manager_cli_calls
            if argv[:3] == ["mgr", "fixture", "populate"]
        ]
        assert populated
        for path in populated:
            assert path.is_file(), f"{path.name} is missing"
            json.loads(path.read_bytes())


class TestKeypairFixture:
    def test_keypair_users_resolve_against_the_users_fixture(self) -> None:
        """The installer derives client env file names from this join."""
        known = {user["uuid"] for user in _load("example-users.json")["users"]}
        keypairs = _load("example-keypairs.json")["keypairs"]

        assert keypairs
        dangling = [kp["access_key"] for kp in keypairs if kp["user"] not in known]
        assert not dangling, f"keypairs reference unknown users: {dangling}"

    @pytest.mark.parametrize(
        ("filename", "collection", "keys"),
        [
            ("example-keypairs.json", "keypairs", ("user", "access_key", "secret_key")),
            ("example-users.json", "users", ("uuid", "username", "email", "password")),
        ],
    )
    def test_keys_the_installer_reads_are_present(
        self, filename: str, collection: str, keys: tuple[str, ...]
    ) -> None:
        rows = _load(filename)[collection]

        assert rows
        for key in keys:
            missing = [index for index, row in enumerate(rows) if key not in row]
            assert not missing, f"{filename}[{collection}][{missing}] lacks {key!r}"
