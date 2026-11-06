import datetime
from uuid import UUID

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from ai.backend.common import typed_validators as tv
from ai.backend.common.dto.appproxy.v2.ingress.types import SessionIngressTarget
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import RouteEntry
from ai.backend.common.exception import BackendAISchemaValidationFailed, InvalidAPIParameters
from ai.backend.common.typed_validators import HostPortPair, KernelHost
from ai.backend.common.types import SessionId

_SESSION_ID = UUID("f5cd34ba-ae53-4537-a813-09f38496443d")
_ROUTE_ID = UUID("4eeb260b-6cc5-4362-baf3-ea978388becd")


def test_time_duration() -> None:
    class NormalModel(BaseModel):
        duration: tv.TimeDuration

    class GenerousModel(BaseModel):
        duration: tv.NaiveTimeDuration

    NormalModel.model_validate({"duration": "3s"})
    NormalModel.model_validate({"duration": "10"})
    NormalModel.model_validate({"duration": "20.5"})
    NormalModel.model_validate({"duration": 8})
    NormalModel.model_validate({"duration": 7.2})
    NormalModel.model_validate({"duration": "2d"})
    NormalModel.model_validate({"duration": "6yr"})
    with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
        NormalModel.model_validate({"duration": "6y"})
    with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
        NormalModel.model_validate({"duration": "6k"})
    with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
        NormalModel.model_validate({"duration": "-6y"})
    GenerousModel.model_validate({"duration": -12})
    GenerousModel.model_validate({"duration": 2})

    NormalModel(duration=datetime.timedelta(days=5)).model_dump_json()


@pytest.mark.parametrize(
    "input, expected",
    [
        ("127.0.0.1:8080", HostPortPair(host="127.0.0.1", port=8080)),
        ("[::1]:443", HostPortPair(host="::1", port=443)),
        (["localhost", 5000], HostPortPair(host="localhost", port=5000)),
        ({"host": "0.0.0.0", "port": 80}, HostPortPair(host="0.0.0.0", port=80)),
        (HostPortPair(host="example.com", port=1234), HostPortPair(host="example.com", port=1234)),
    ],
)
def test_hostport_pair_valid(
    input: str | list[str | int] | dict[str, str | int] | HostPortPair, expected: HostPortPair
) -> None:
    result = HostPortPair.model_validate(input)
    assert result == expected
    assert result.address == f"{expected.host}:{expected.port}"


@pytest.mark.parametrize(
    "input",
    [
        "127.0.0.1",
        "127.0.0.1:70000",
        "127.0.0.1:notaport",
        ["127.0.0.1"],
        {"host": "127.0.0.1"},
        1234,
    ],
)
def test_hostport_pair_invalid(input: str | list[str] | dict[str, str] | int) -> None:
    with pytest.raises((BackendAISchemaValidationFailed, ValidationError, TypeError)):
        HostPortPair.model_validate(input)


class _HealthCheckModel(BaseModel):
    path: tv.HealthCheckPath


class TestHealthCheckPath:
    @pytest.mark.parametrize(
        "path",
        ["health", "@evil.example/x", "//evil.example/x", "http://evil.example/x"],
    )
    def test_rejects_path_with_host_or_without_leading_slash(self, path: str) -> None:
        with pytest.raises(InvalidAPIParameters):
            _HealthCheckModel.model_validate({"path": path})

    @pytest.mark.parametrize("path", ["/health", "/health?x=1", "/a@b/x"])
    def test_allows_absolute_path(self, path: str) -> None:
        assert _HealthCheckModel.model_validate({"path": path}).path == path


class TestKernelHost:
    @pytest.mark.parametrize(
        "kernel_host",
        [
            "10.0.0.1",
            "172.17.0.2",
            "192.168.1.100",
            "fd00::1",
            "127.0.0.1",
            "::1",
            "localhost",
            "agent-1.example.com",
            "agent_1",
        ],
    )
    def test_accepts_the_kernel_host(self, kernel_host: str) -> None:
        assert TypeAdapter(KernelHost).validate_python(kernel_host) == kernel_host

    @pytest.mark.parametrize(
        "kernel_host",
        [
            "169.254.169.254",
            "::ffff:169.254.169.254",
            "fe80::1",
            "2852039166",
            "169.254.43518",
            "0xa9.0xfe.0xa9.0xfe",
            "169.254.169.254.",
            "",
            "host name",
            "host/path",
            "user@host",
            "host:80",
            "10.0.0.1\nbackend=10.0.0.2,80",
        ],
    )
    def test_rejects_the_kernel_host(self, kernel_host: str) -> None:
        with pytest.raises(ValidationError):
            TypeAdapter(KernelHost).validate_python(kernel_host)


class TestModelsWithAKernelHost:
    def test_route_entry_rejects_a_metadata_address(self) -> None:
        with pytest.raises(ValidationError):
            RouteEntry(
                session_id=_SESSION_ID,
                route_id=_ROUTE_ID,
                kernel_host="169.254.169.254",
                kernel_port=80,
            )

    def test_session_ingress_target_rejects_a_metadata_address(self) -> None:
        with pytest.raises(ValidationError):
            SessionIngressTarget(
                host="169.254.169.254",
                port=80,
                session_id=SessionId(_SESSION_ID),
            )
