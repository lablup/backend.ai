from __future__ import annotations

import asyncio
import socket
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from etcd_client import GRPCStatusError

from ai.backend.common.configs.etcd import EtcdConfig, EtcdTLSConfig
from ai.backend.common.data.config.types import EtcdConfigData, EtcdTLSConfigData
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.typed_validators import HostPortPair

_HANDSHAKE_TIMEOUT_SECONDS = 0.2
_OPEN_WAIT_LIMIT_SECONDS = 5.0


@dataclass(frozen=True)
class _RejectedTLSConfigCase:
    keys_set_to_a_pem_file: tuple[str, ...]
    keys_set_to_a_missing_file: tuple[str, ...]
    expected_error: str


@dataclass(frozen=True)
class _HandshakeTimeoutConversionCase:
    handshake_timeout: float
    expected_handshake_timeout: float | None


@dataclass(frozen=True)
class _EndpointSchemeCase:
    tls_enabled: bool
    expected_endpoint: str


@pytest.fixture
def pem_file(tmp_path: Path) -> Path:
    path = tmp_path / "certificate.pem"
    path.write_bytes(b"pem-file-content")
    return path


@pytest.fixture
def raw_tls_config_of_case(
    case: _RejectedTLSConfigCase, pem_file: Path, tmp_path: Path
) -> dict[str, Any]:
    return {
        "enabled": True,
        **dict.fromkeys(case.keys_set_to_a_pem_file, pem_file),
        **dict.fromkeys(case.keys_set_to_a_missing_file, tmp_path / "missing.pem"),
    }


@pytest.fixture
def etcd_config_data_of_case(case: _EndpointSchemeCase, pem_file: Path) -> EtcdConfigData:
    return EtcdConfig.model_validate({
        "addrs": [{"host": "127.0.0.1", "port": 2379}],
        "user": "etcd-user",
        "password": "etcd-password",
        "tls": {"enabled": case.tls_enabled, "ca-cert": pem_file},
    }).to_dataclass()


@pytest.fixture
def enabled_tls_config_of_case(
    case: _HandshakeTimeoutConversionCase, pem_file: Path
) -> EtcdTLSConfig:
    return EtcdTLSConfig.model_validate({
        "enabled": True,
        "ca-cert": pem_file,
        "client-cert": pem_file,
        "client-key": pem_file,
        "handshake-timeout": case.handshake_timeout,
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
                    enabled=True,
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
                keys_set_to_a_pem_file=(),
                keys_set_to_a_missing_file=(),
                expected_error="ca-cert is required",
            ),
            _RejectedTLSConfigCase(
                keys_set_to_a_pem_file=("ca-cert", "client-cert"),
                keys_set_to_a_missing_file=(),
                expected_error="must be set together",
            ),
            _RejectedTLSConfigCase(
                keys_set_to_a_pem_file=("ca-cert", "client-key"),
                keys_set_to_a_missing_file=(),
                expected_error="must be set together",
            ),
            _RejectedTLSConfigCase(
                keys_set_to_a_pem_file=(),
                keys_set_to_a_missing_file=("ca-cert",),
                expected_error="ca-cert",
            ),
        ],
    )
    def test_rejects_invalid_certificates(
        self, case: _RejectedTLSConfigCase, raw_tls_config_of_case: dict[str, Any]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match=case.expected_error):
            EtcdTLSConfig.model_validate(raw_tls_config_of_case)

    @pytest.mark.parametrize(
        "case",
        [
            _HandshakeTimeoutConversionCase(handshake_timeout=1.5, expected_handshake_timeout=1.5),
            _HandshakeTimeoutConversionCase(handshake_timeout=0, expected_handshake_timeout=None),
        ],
        ids=lambda case: f"handshake-timeout-{case.handshake_timeout}",
    )
    def test_enabled_config_converts_to_data(
        self,
        case: _HandshakeTimeoutConversionCase,
        enabled_tls_config_of_case: EtcdTLSConfig,
        pem_file: Path,
    ) -> None:
        assert enabled_tls_config_of_case.to_dataclass() == EtcdTLSConfigData(
            enabled=True,
            ca_cert=pem_file,
            client_cert=pem_file,
            client_key=pem_file,
            handshake_timeout=case.expected_handshake_timeout,
        )


class TestAsyncEtcdOverTLS:
    @pytest.mark.parametrize(
        "case",
        [
            _EndpointSchemeCase(tls_enabled=True, expected_endpoint="https://127.0.0.1:2379"),
            _EndpointSchemeCase(tls_enabled=False, expected_endpoint="http://127.0.0.1:2379"),
        ],
        ids=lambda case: f"tls-enabled-{case.tls_enabled}",
    )
    def test_tls_enabled_selects_endpoint_scheme(
        self, case: _EndpointSchemeCase, etcd_config_data_of_case: EtcdConfigData
    ) -> None:
        with patch("ai.backend.common.etcd.EtcdClient") as etcd_client_cls:
            AsyncEtcd.create_from_config(etcd_config_data_of_case)

        assert etcd_client_cls.call_args.args[0] == [case.expected_endpoint]

    async def test_handshake_timeout_ends_open_on_silent_server(
        self, etcd_of_server_silent_during_handshake: AsyncEtcd
    ) -> None:
        with pytest.raises(GRPCStatusError, match="TLS handshake timeout"):
            await asyncio.wait_for(
                etcd_of_server_silent_during_handshake.open(), _OPEN_WAIT_LIMIT_SECONDS
            )
