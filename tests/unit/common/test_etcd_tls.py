from __future__ import annotations

import asyncio
import socket
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from etcd_client import GRPCStatusError

from ai.backend.common.configs.etcd import EtcdTLSConfig
from ai.backend.common.data.config.types import EtcdConfigData, EtcdTLSConfigData
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.typed_validators import HostPortPair

_HANDSHAKE_TIMEOUT_SECONDS = 0.2
_OPEN_WAIT_LIMIT_SECONDS = 5.0


@dataclass(frozen=True)
class _RejectedTLSConfigCase:
    enabled: bool
    keys_set_to_a_pem_file: tuple[str, ...]
    expected_error: str


@pytest.fixture
def pem_file(tmp_path: Path) -> Path:
    path = tmp_path / "certificate.pem"
    path.write_bytes(b"pem-file-content")
    return path


@pytest.fixture
def raw_tls_config_of_case(case: _RejectedTLSConfigCase, pem_file: Path) -> dict[str, Any]:
    return {"enabled": case.enabled, **dict.fromkeys(case.keys_set_to_a_pem_file, pem_file)}


@pytest.fixture
def disabled_tls_config_with_certificates(pem_file: Path) -> EtcdTLSConfig:
    return EtcdTLSConfig.model_validate({"enabled": False, "ca-cert": pem_file})


@pytest.fixture
def enabled_tls_config_with_client_certificate(pem_file: Path) -> EtcdTLSConfig:
    return EtcdTLSConfig.model_validate({
        "enabled": True,
        "ca-cert": pem_file,
        "client-cert": pem_file,
        "client-key": pem_file,
        "handshake-timeout": 1.5,
    })


@pytest.fixture
def enabled_tls_config_with_no_handshake_limit(pem_file: Path) -> EtcdTLSConfig:
    return EtcdTLSConfig.model_validate({
        "enabled": True,
        "ca-cert": pem_file,
        "handshake-timeout": 0,
    })


@pytest.fixture
def etcd_of_server_silent_during_handshake(pem_file: Path) -> Iterator[AsyncEtcd]:
    with socket.create_server(("127.0.0.1", 0)) as silent_server:
        yield AsyncEtcd.create_from_config(
            EtcdConfigData(
                namespace="test",
                addrs=[HostPortPair(host="127.0.0.1", port=silent_server.getsockname()[1])],
                user="etcd-user",
                password="etcd-password",
                keep_alive_interval=5.0,
                keep_alive_timeout=3.0,
                tls=EtcdTLSConfigData(
                    ca_cert=pem_file,
                    client_cert=None,
                    client_key=None,
                    handshake_timeout=_HANDSHAKE_TIMEOUT_SECONDS,
                ),
            )
        )


class TestEtcdTLSConfig:
    @pytest.mark.parametrize(
        "case",
        [
            _RejectedTLSConfigCase(
                enabled=True,
                keys_set_to_a_pem_file=(),
                expected_error="ca-cert is required",
            ),
            _RejectedTLSConfigCase(
                enabled=True,
                keys_set_to_a_pem_file=("ca-cert", "client-cert"),
                expected_error="must be set together",
            ),
            _RejectedTLSConfigCase(
                enabled=True,
                keys_set_to_a_pem_file=("ca-cert", "client-key"),
                expected_error="must be set together",
            ),
        ],
        ids=lambda case: "-".join(case.keys_set_to_a_pem_file) or "no-certificates",
    )
    def test_rejects_incomplete_certificates(
        self, case: _RejectedTLSConfigCase, raw_tls_config_of_case: dict[str, Any]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match=case.expected_error):
            EtcdTLSConfig.model_validate(raw_tls_config_of_case)

    def test_rejects_certificate_file_that_does_not_exist(self, tmp_path: Path) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match="ca-cert"):
            EtcdTLSConfig.model_validate({"enabled": True, "ca-cert": tmp_path / "missing.pem"})

    def test_disabled_config_converts_to_none(
        self, disabled_tls_config_with_certificates: EtcdTLSConfig
    ) -> None:
        assert disabled_tls_config_with_certificates.to_dataclass() is None

    def test_enabled_config_converts_to_data(
        self, enabled_tls_config_with_client_certificate: EtcdTLSConfig, pem_file: Path
    ) -> None:
        assert enabled_tls_config_with_client_certificate.to_dataclass() == EtcdTLSConfigData(
            ca_cert=pem_file,
            client_cert=pem_file,
            client_key=pem_file,
            handshake_timeout=1.5,
        )

    def test_zero_handshake_timeout_converts_to_no_limit(
        self, enabled_tls_config_with_no_handshake_limit: EtcdTLSConfig, pem_file: Path
    ) -> None:
        assert enabled_tls_config_with_no_handshake_limit.to_dataclass() == EtcdTLSConfigData(
            ca_cert=pem_file,
            client_cert=None,
            client_key=None,
            handshake_timeout=None,
        )


class TestAsyncEtcdOverTLS:
    async def test_handshake_timeout_ends_open_on_silent_server(
        self, etcd_of_server_silent_during_handshake: AsyncEtcd
    ) -> None:
        with pytest.raises(GRPCStatusError, match="TLS handshake timeout"):
            await asyncio.wait_for(
                etcd_of_server_silent_during_handshake.open(), _OPEN_WAIT_LIMIT_SECONDS
            )
