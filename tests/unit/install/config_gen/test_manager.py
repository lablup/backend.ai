"""Tests for shared Manager config generation."""

from __future__ import annotations

import pytest
import tomlkit

from ai.backend.install.config_gen.manager import (
    ManagerParams,
    apply_manager_config,
)

MANAGER_SAMPLE = """\
[etcd]
namespace = "local"
[etcd.addr]
host = "127.0.0.1"
port = 8120

[db]
[db.addr]
host = "127.0.0.1"
port = 8100

[manager]
# Manager service address
num-proc = 4
ipc-base-path = "/tmp/backend.ai/ipc"
[manager.service-addr]
host = "0.0.0.0"
port = 8081
"""


def _load_doc() -> tomlkit.TOMLDocument:
    return tomlkit.loads(MANAGER_SAMPLE)


class TestApplyManagerConfig:
    @pytest.fixture()
    def params(self) -> ManagerParams:
        return ManagerParams(
            etcd_port=2379,
            db_port=5432,
            manager_port=8091,
            num_proc=1,
            ipc_base_path="ipc/manager",
        )

    def test_etcd_port(self, params: ManagerParams) -> None:
        doc = _load_doc()
        apply_manager_config(doc, params)
        assert doc["etcd"]["addr"]["port"] == 2379

    def test_db_port(self, params: ManagerParams) -> None:
        doc = _load_doc()
        apply_manager_config(doc, params)
        assert doc["db"]["addr"]["port"] == 5432

    def test_manager_port(self, params: ManagerParams) -> None:
        doc = _load_doc()
        apply_manager_config(doc, params)
        assert doc["manager"]["service-addr"]["port"] == 8091

    def test_num_proc(self, params: ManagerParams) -> None:
        doc = _load_doc()
        apply_manager_config(doc, params)
        assert doc["manager"]["num-proc"] == 1

    def test_ipc_base_path(self, params: ManagerParams) -> None:
        doc = _load_doc()
        apply_manager_config(doc, params)
        assert doc["manager"]["ipc-base-path"] == "ipc/manager"

    def test_comments_preserved(self, params: ManagerParams) -> None:
        doc = _load_doc()
        apply_manager_config(doc, params)
        output = tomlkit.dumps(doc)
        assert "# Manager service address" in output

    def test_toml_roundtrip(self, params: ManagerParams) -> None:
        doc = _load_doc()
        apply_manager_config(doc, params)
        output = tomlkit.dumps(doc)
        reparsed = tomlkit.loads(output)
        assert reparsed["etcd"]["addr"]["port"] == 2379
        assert reparsed["manager"]["num-proc"] == 1
