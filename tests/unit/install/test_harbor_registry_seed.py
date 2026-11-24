from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, override

import pytest
from ruamel.yaml import YAML

from ai.backend.install.context import Context
from ai.backend.install.types import HarborOptions

DEFAULT_DOMAIN_ID = "b9e676dc-e23e-54c6-b350-e83fba4127e9"


class _HarborSeedContext(Context):
    applied_paths: list[Path]

    def __init__(self, base_path: Path) -> None:
        self.install_info = type("_InstallInfo", (), {"base_path": base_path})()
        self.applied_paths = []

    @override
    def hydrate_install_info(self) -> Any:
        raise NotImplementedError

    @override
    def log_header(self, title: str) -> None:
        pass

    @override
    async def run_manager_cli(self, cmdargs: Sequence[str]) -> None:
        assert list(cmdargs[:3]) == ["mgr", "seed", "apply"]
        self.applied_paths.extend(Path(arg) for arg in cmdargs[3:])


@pytest.fixture
def harbor_context(tmp_path: Path) -> _HarborSeedContext:
    (tmp_path / "harbor").mkdir()
    return _HarborSeedContext(tmp_path)


def _applied_items(paths: Sequence[Path], kind: str) -> list[dict[str, Any]]:
    yaml = YAML(typ="safe")
    items: list[dict[str, Any]] = []
    for path in paths:
        document = yaml.load(path.read_text(encoding="utf8"))
        if document["kind"] == kind:
            items.extend(document["items"])
    return items


class TestRegisterLocalHarborRegistry:
    async def test_relates_the_default_domain_to_the_registered_harbor(
        self, harbor_context: _HarborSeedContext
    ) -> None:
        await harbor_context._register_local_harbor_registry(
            HarborOptions(hostname="10.0.0.1", http_port=8085, admin_password="secret")
        )

        registries = _applied_items(harbor_context.applied_paths, "container_registry")
        relations = _applied_items(harbor_context.applied_paths, "domain_container_registry")
        assert [r["registry_name"] for r in registries] == ["10.0.0.1:8085"]
        assert relations == [{"domain_id": DEFAULT_DOMAIN_ID, "registry_id": registries[0]["id"]}]
