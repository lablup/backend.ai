from __future__ import annotations

from pathlib import Path
from typing import Any, override

import pytest
from ruamel.yaml import YAML

from ai.backend.common.types import HostPortPair
from ai.backend.install.context import Context
from ai.backend.install.types import ServerAddr, SftpAgentOptions

DEFAULT_DOMAIN_ID = "b9e676dc-e23e-54c6-b350-e83fba4127e9"


class _InstallSeedsContext(Context):
    def __init__(self) -> None:
        coordinator_addr = ServerAddr(HostPortPair("127.0.0.1", 10200))
        sftp_agent = SftpAgentOptions(
            rpc_addr=ServerAddr(HostPortPair("127.0.0.1", 6013)),
            watcher_addr=ServerAddr(HostPortPair("127.0.0.1", 6015)),
            sock_port=6017,
            ipc_base_path="ipc",
            var_base_path="var",
            scaling_group="sftp",
        )
        service = type(
            "_ServiceConfig",
            (),
            {
                "appproxy_coordinator_addr": coordinator_addr,
                "appproxy_api_secret": "secret",
                "sftp_agent": sftp_agent,
            },
        )()
        self.install_info = type("_InstallInfo", (), {"service_config": service})()

    @override
    def hydrate_install_info(self) -> Any:
        raise NotImplementedError

    @override
    def log_header(self, title: str) -> None:
        pass


@pytest.fixture
def sftp_install_context() -> _InstallSeedsContext:
    return _InstallSeedsContext()


class TestWriteInstallSeeds:
    def test_allows_the_sftp_resource_group_to_the_default_domain(
        self, sftp_install_context: _InstallSeedsContext, tmp_path: Path
    ) -> None:
        with Context.resource_path("ai.backend.install.seeds", "manager") as manager_seeds:
            sftp_install_context.write_install_seeds(manager_seeds, tmp_path)

        yaml = YAML(typ="safe")
        resource_groups = yaml.load((tmp_path / "resource_group.yaml").read_text())
        relations = yaml.load((tmp_path / "resource_group_for_domain.yaml").read_text())
        sftp_group = next(item for item in resource_groups["items"] if item["name"] == "sftp")
        assert relations == {
            "kind": "resource_group_for_domain",
            "version": 1,
            "items": [{"domain_id": DEFAULT_DOMAIN_ID, "resource_group_id": sftp_group["id"]}],
        }
