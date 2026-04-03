"""Tests for shared Storage Proxy config generation."""

from __future__ import annotations

import pytest
import tomlkit

from ai.backend.install.config_gen.storage_proxy import (
    StorageProxyParams,
    apply_storage_proxy_config,
)

STORAGE_PROXY_SAMPLE = """\
[etcd]
namespace = "local"
addr = { host = "127.0.0.1", port = 8120 }
user = ""
password = ""

[storage-proxy]
secret = "placeholder"
ipc-base-path = "ipc/storage-proxy"

[api.client]
service-addr = { host = "0.0.0.0", port = 6021 }

[api.manager]
service-addr = { host = "127.0.0.1", port = 6022 }
secret = "placeholder"
ssl-verify = false

[volume.volume1]
backend = "vfs"
path = "vfolder/local/volume1"
"""


def _load_doc() -> tomlkit.TOMLDocument:
    return tomlkit.loads(STORAGE_PROXY_SAMPLE)


class TestApplyStorageProxyConfig:
    @pytest.fixture()
    def params(self) -> StorageProxyParams:
        return StorageProxyParams(
            etcd_host="10.0.0.1",
            etcd_port=2379,
            secret="my-secret",
            manager_secret="mgr-auth-key",
            volume_path="vfolder/nfs/data",
        )

    def test_etcd_config(self, params: StorageProxyParams) -> None:
        doc = _load_doc()
        apply_storage_proxy_config(doc, params)
        assert doc["etcd"]["addr"]["host"] == "10.0.0.1"
        assert doc["etcd"]["addr"]["port"] == 2379
        assert doc["etcd"]["namespace"] == "local"

    def test_etcd_credentials(self) -> None:
        params = StorageProxyParams(etcd_user="admin", etcd_password="pass")
        doc = _load_doc()
        apply_storage_proxy_config(doc, params)
        assert doc["etcd"]["user"] == "admin"
        assert doc["etcd"]["password"] == "pass"

    def test_etcd_no_credentials(self, params: StorageProxyParams) -> None:
        doc = _load_doc()
        apply_storage_proxy_config(doc, params)
        assert "user" not in doc["etcd"]
        assert "password" not in doc["etcd"]

    def test_storage_proxy_secret(self, params: StorageProxyParams) -> None:
        doc = _load_doc()
        apply_storage_proxy_config(doc, params)
        assert doc["storage-proxy"]["secret"] == "my-secret"

    def test_client_addr(self) -> None:
        params = StorageProxyParams(client_host="0.0.0.0", client_port=7021)
        doc = _load_doc()
        apply_storage_proxy_config(doc, params)
        assert doc["api"]["client"]["service-addr"]["host"] == "0.0.0.0"
        assert doc["api"]["client"]["service-addr"]["port"] == 7021

    def test_manager_addr_and_secret(self, params: StorageProxyParams) -> None:
        doc = _load_doc()
        apply_storage_proxy_config(doc, params)
        assert doc["api"]["manager"]["secret"] == "mgr-auth-key"

    def test_volume_path(self, params: StorageProxyParams) -> None:
        doc = _load_doc()
        apply_storage_proxy_config(doc, params)
        assert doc["volume"]["volume1"]["path"] == "vfolder/nfs/data"

    def test_toml_roundtrip(self, params: StorageProxyParams) -> None:
        doc = _load_doc()
        apply_storage_proxy_config(doc, params)
        output = tomlkit.dumps(doc)
        reparsed = tomlkit.loads(output)
        assert reparsed["etcd"]["addr"]["host"] == "10.0.0.1"
        assert reparsed["storage-proxy"]["secret"] == "my-secret"
        assert reparsed["api"]["manager"]["secret"] == "mgr-auth-key"
