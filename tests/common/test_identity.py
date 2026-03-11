from __future__ import annotations

import json
import random
import secrets
import socket
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import aiodns
import aiohttp
import pytest
from aioresponses import aioresponses

import ai.backend.common.identity
from ai.backend.common.exception import CloudDetectionError
from ai.backend.common.identity import (
    CloudProvider,
    _detect_aws,
    _detect_azure,
    _detect_gcp,
    detect_cloud,
)


def test_is_containerized():
    mocked_path = MagicMock()
    mocked_path.read_text.return_value = "\n".join([
        "13:name=systemd:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "12:pids:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "11:hugetlb:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "10:net_prio:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "9:perf_event:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "8:net_cls:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "7:freezer:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "6:devices:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "5:memory:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "4:blkio:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "3:cpuacct:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "2:cpu:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
        "1:cpuset:/docker-ce/docker/67bfa4f7a0d87eb95592dd95ce851fe6625db539fa2ea616000202b328c32c92",
    ])
    with patch("ai.backend.common.identity.Path", return_value=mocked_path):
        assert ai.backend.common.identity.is_containerized()
    mocked_path = MagicMock()
    mocked_path.read_text.return_value = "\n".join([
        "11:devices:/user.slice",
        "10:pids:/user.slice/user-1000.slice",
        "9:hugetlb:/",
        "8:cpuset:/",
        "7:blkio:/user.slice",
        "6:memory:/user.slice",
        "5:cpu,cpuacct:/user.slice",
        "4:freezer:/",
        "3:net_cls,net_prio:/",
        "2:perf_event:/",
        "1:name=systemd:/user.slice/user-1000.slice/session-3.scope",
    ])
    with patch("ai.backend.common.identity.Path", return_value=mocked_path):
        assert not ai.backend.common.identity.is_containerized()
    mocked_path = MagicMock()
    mocked_path.side_effect = FileNotFoundError("no such file")
    with patch("ai.backend.common.identity.Path", return_value=mocked_path):
        assert not ai.backend.common.identity.is_containerized()


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["amazon", "google", "azure", None])
async def test_get_instance_id(mocker, provider):
    ai.backend.common.identity.current_provider = provider
    ai.backend.common.identity._defined = False
    ai.backend.common.identity._define_functions()

    with aioresponses() as m:
        random_id = secrets.token_hex(16)
        if provider == "amazon":
            m.get("http://169.254.169.254/latest/meta-data/instance-id", body=random_id)
            ret = await ai.backend.common.identity.get_instance_id()
            assert ret == random_id
        elif provider == "azure":
            m.get(
                "http://169.254.169.254/metadata/instance?version=2017-03-01",
                payload={
                    "compute": {
                        "vmId": random_id,
                    },
                },
            )
            ret = await ai.backend.common.identity.get_instance_id()
            assert ret == random_id
        elif provider == "google":
            m.get("http://metadata.google.internal/computeMetadata/v1/instance/id", body=random_id)
            ret = await ai.backend.common.identity.get_instance_id()
            assert ret == random_id
        elif provider is None:
            with patch("socket.gethostname", return_value="myname"):
                ret = await ai.backend.common.identity.get_instance_id()
                assert ret == "i-myname"


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["amazon", "google", "azure", None])
async def test_get_instance_id_failures(mocker, provider):
    ai.backend.common.identity.current_provider = provider
    ai.backend.common.identity._defined = False
    ai.backend.common.identity._define_functions()

    with aioresponses():
        # If we don't set any mocked responses, aioresponses will raise ClientConnectionError.
        ret = await ai.backend.common.identity.get_instance_id()
        assert ret == f"i-{socket.gethostname()}"


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["amazon", "google", "azure", None])
async def test_get_instance_ip(mocker, provider):
    ai.backend.common.identity.current_provider = provider
    ai.backend.common.identity._defined = False
    ai.backend.common.identity._define_functions()

    with aioresponses() as m:
        random_ip = ".".join(str(random.randint(0, 255)) for _ in range(4))
        if provider == "amazon":
            m.get("http://169.254.169.254/latest/meta-data/local-ipv4", body=random_ip)
            ret = await ai.backend.common.identity.get_instance_ip()
            assert ret == random_ip
        elif provider == "azure":
            m.get(
                "http://169.254.169.254/metadata/instance?version=2017-03-01",
                payload={
                    "network": {
                        "interface": [
                            {
                                "ipv4": {
                                    "ipaddress": [
                                        {"ipaddress": random_ip},
                                    ],
                                },
                            },
                        ],
                    },
                },
            )
            ret = await ai.backend.common.identity.get_instance_ip()
            assert ret == random_ip
        elif provider == "google":
            m.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip",
                body=random_ip,
            )
            ret = await ai.backend.common.identity.get_instance_ip()
            assert ret == random_ip
        elif provider is None:
            mocked_ares_host_result = MagicMock()
            mocked_ares_host_result.addresses = ["10.1.2.3"]
            mocked_resolver = MagicMock()

            async def coro_return_mocked_result(*args):
                return mocked_ares_host_result

            mocked_resolver.gethostbyname = coro_return_mocked_result
            with (
                patch("aiodns.DNSResolver", return_value=mocked_resolver),
                patch("socket.gethostname", return_value="myname"),
            ):
                ret = await ai.backend.common.identity.get_instance_ip()
                assert ret == "10.1.2.3"

            async def coro_raise_error(*args):
                raise aiodns.error.DNSError("domain not found")

            mocked_resolver = MagicMock()
            mocked_resolver.gethostbyname = coro_raise_error
            with (
                patch("aiodns.DNSResolver", return_value=mocked_resolver),
                patch("socket.gethostname", return_value="myname"),
            ):
                ret = await ai.backend.common.identity.get_instance_ip()
                assert ret == "127.0.0.1"


@pytest.mark.skip
@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["amazon", "google", "azure", None])
async def test_get_instance_type(mocker, provider):
    ai.backend.common.identity.current_provider = provider
    ai.backend.common.identity._defined = False
    ai.backend.common.identity._define_functions()

    with aioresponses() as m:
        random_type = secrets.token_hex(16)
        if provider == "amazon":
            m.get("http://169.254.169.254/latest/meta-data/instance-type", body=random_type)
            ret = await ai.backend.common.identity.get_instance_type()
            assert ret == random_type
        elif provider == "azure":
            m.get(
                "http://169.254.169.254/metadata/instance?version=2017-03-01",
                payload={
                    "compute": {
                        "vmSize": random_type,
                    },
                },
            )
            ret = await ai.backend.common.identity.get_instance_type()
            assert ret == random_type
        elif provider == "google":
            m.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/machine-type",
                body=random_type,
            )
            ret = await ai.backend.common.identity.get_instance_type()
            assert ret == random_type
        elif provider is None:
            ret = await ai.backend.common.identity.get_instance_type()
            assert ret == "default"


_AWS_URL = "http://169.254.169.254/latest/meta-data/"
_AZURE_URL = "http://169.254.169.254/metadata/instance/compute?api-version=2021-02-01"
_GCP_URL = "http://169.254.169.254/computeMetadata/v1/instance/id"


class TestDetectCloudServices:
    @pytest.fixture
    def mock_responses(self) -> Generator[aioresponses, None, None]:
        with aioresponses() as m:
            yield m

    @pytest.fixture
    async def client_session(
        self, mock_responses: aioresponses
    ) -> AsyncGenerator[aiohttp.ClientSession, None]:
        async with aiohttp.ClientSession() as session:
            yield session

    @pytest.fixture
    def aws_metadata_url(self) -> str:
        return _AWS_URL

    async def test_valid_aws_metadata(
        self,
        mock_responses: aioresponses,
        client_session: aiohttp.ClientSession,
        aws_metadata_url: str,
    ) -> None:
        mock_responses.get(
            aws_metadata_url,
            body="ami-id\nami-launch-index\ninstance-id\ninstance-type\nlocal-hostname",
        )
        result = await _detect_aws(client_session)
        assert result == CloudProvider.AWS

    @pytest.mark.parametrize(
        "body",
        ["<html>Cloud metadata</html>", ""],
        ids=["non_aws_body", "empty_body"],
    )
    async def test_rejects_non_aws_response(
        self,
        mock_responses: aioresponses,
        client_session: aiohttp.ClientSession,
        aws_metadata_url: str,
        body: str,
    ) -> None:
        mock_responses.get(aws_metadata_url, body=body)
        with pytest.raises(CloudDetectionError, match="AWS detection failed"):
            await _detect_aws(client_session)

    @pytest.mark.parametrize("status", [404, 500, 503], ids=["404", "500", "503"])
    async def test_rejects_non_200_aws_response(
        self,
        mock_responses: aioresponses,
        client_session: aiohttp.ClientSession,
        aws_metadata_url: str,
        status: int,
    ) -> None:
        mock_responses.get(aws_metadata_url, status=status, body="error")
        with pytest.raises(CloudDetectionError, match=f"AWS detection failed with status {status}"):
            await _detect_aws(client_session)

    @pytest.fixture
    def azure_metadata_url(self) -> str:
        return _AZURE_URL

    async def test_valid_azure_metadata(
        self,
        mock_responses: aioresponses,
        client_session: aiohttp.ClientSession,
        azure_metadata_url: str,
    ) -> None:
        mock_responses.get(
            azure_metadata_url,
            body=json.dumps({"vmId": "abc-123", "name": "myvm", "vmSize": "Standard_D2s_v3"}),
        )
        result = await _detect_azure(client_session)
        assert result == CloudProvider.AZURE

    @pytest.mark.parametrize(
        "body",
        [
            "not json at all",
            json.dumps({"someOtherKey": "value"}),
            "",
        ],
        ids=["non_json", "json_without_vmid", "empty_body"],
    )
    async def test_rejects_non_azure_response(
        self,
        mock_responses: aioresponses,
        client_session: aiohttp.ClientSession,
        azure_metadata_url: str,
        body: str,
    ) -> None:
        mock_responses.get(azure_metadata_url, body=body)
        with pytest.raises(CloudDetectionError, match="Azure detection failed"):
            await _detect_azure(client_session)

    @pytest.mark.parametrize("status", [404, 500, 503], ids=["404", "500", "503"])
    async def test_rejects_non_200_azure_response(
        self,
        mock_responses: aioresponses,
        client_session: aiohttp.ClientSession,
        azure_metadata_url: str,
        status: int,
    ) -> None:
        mock_responses.get(azure_metadata_url, status=status, body="error")
        with pytest.raises(
            CloudDetectionError, match=f"Azure detection failed with status {status}"
        ):
            await _detect_azure(client_session)

    @pytest.fixture
    def gcp_metadata_url(self) -> str:
        return _GCP_URL

    async def test_valid_gcp_metadata(
        self,
        mock_responses: aioresponses,
        client_session: aiohttp.ClientSession,
        gcp_metadata_url: str,
    ) -> None:
        mock_responses.get(gcp_metadata_url, body="1234567890123456")
        result = await _detect_gcp(client_session)
        assert result == CloudProvider.GCP

    @pytest.mark.parametrize(
        "body",
        ["not-a-number", ""],
        ids=["non_numeric", "empty_body"],
    )
    async def test_rejects_non_gcp_response(
        self,
        mock_responses: aioresponses,
        client_session: aiohttp.ClientSession,
        gcp_metadata_url: str,
        body: str,
    ) -> None:
        mock_responses.get(gcp_metadata_url, body=body)
        with pytest.raises(CloudDetectionError, match="GCP detection failed"):
            await _detect_gcp(client_session)

    @pytest.mark.parametrize("status", [404, 500, 503], ids=["404", "500", "503"])
    async def test_rejects_non_200_gcp_response(
        self,
        mock_responses: aioresponses,
        client_session: aiohttp.ClientSession,
        gcp_metadata_url: str,
        status: int,
    ) -> None:
        mock_responses.get(gcp_metadata_url, status=status, body="error")
        with pytest.raises(CloudDetectionError, match=f"GCP detection failed with status {status}"):
            await _detect_gcp(client_session)


@dataclass(frozen=True)
class IMDSMock:
    """Mocked IMDS endpoint response specification."""

    body: str = ""
    status: int = 200


@dataclass(frozen=True)
class DetectCloudScenario:
    """Bundled scenario for detect_cloud() parametrized tests."""

    aws: IMDSMock
    azure: IMDSMock
    gcp: IMDSMock
    expected: CloudProvider | None


class TestDetectCloud:
    @pytest.fixture
    def mock_responses(self) -> Generator[aioresponses, None, None]:
        with aioresponses() as m:
            yield m

    @pytest.mark.parametrize(
        "scenario",
        [
            pytest.param(
                DetectCloudScenario(
                    aws=IMDSMock(body="ami-id\ninstance-id\ninstance-type"),
                    azure=IMDSMock(status=404),
                    gcp=IMDSMock(status=404),
                    expected=CloudProvider.AWS,
                ),
                id="aws_wins",
            ),
            pytest.param(
                DetectCloudScenario(
                    aws=IMDSMock(status=404),
                    azure=IMDSMock(body=json.dumps({"vmId": "abc-123"})),
                    gcp=IMDSMock(status=404),
                    expected=CloudProvider.AZURE,
                ),
                id="azure_wins",
            ),
            pytest.param(
                DetectCloudScenario(
                    aws=IMDSMock(status=404),
                    azure=IMDSMock(status=404),
                    gcp=IMDSMock(body="1234567890123456"),
                    expected=CloudProvider.GCP,
                ),
                id="gcp_wins",
            ),
            pytest.param(
                DetectCloudScenario(
                    aws=IMDSMock(status=404),
                    azure=IMDSMock(status=404),
                    gcp=IMDSMock(status=404),
                    expected=None,
                ),
                id="all_non_200",
            ),
        ],
    )
    async def test_detect_cloud(
        self,
        mock_responses: aioresponses,
        scenario: DetectCloudScenario,
    ) -> None:
        mock_responses.get(_AWS_URL, status=scenario.aws.status, body=scenario.aws.body)
        mock_responses.get(_AZURE_URL, status=scenario.azure.status, body=scenario.azure.body)
        mock_responses.get(_GCP_URL, status=scenario.gcp.status, body=scenario.gcp.body)
        result = await detect_cloud()
        assert result == scenario.expected

    async def test_detect_cloud_returns_none_on_network_errors(
        self,
        mock_responses: aioresponses,
    ) -> None:
        mock_responses.get(_AWS_URL, exception=aiohttp.ClientConnectionError())
        mock_responses.get(_AZURE_URL, exception=aiohttp.ClientConnectionError())
        mock_responses.get(_GCP_URL, exception=aiohttp.ClientConnectionError())
        result = await detect_cloud()
        assert result is None

    async def test_detect_cloud_picks_valid_when_others_fail(
        self,
        mock_responses: aioresponses,
    ) -> None:
        mock_responses.get(_AWS_URL, body="<html>not aws</html>")
        mock_responses.get(_AZURE_URL, exception=aiohttp.ClientConnectionError())
        mock_responses.get(_GCP_URL, body="1234567890123456")
        result = await detect_cloud()
        assert result == CloudProvider.GCP


class TestIdentityFunctions:
    @pytest.fixture
    def mock_curl(self) -> Generator[AsyncMock, None, None]:
        mock = AsyncMock()
        with patch("ai.backend.common.identity.curl", mock):
            yield mock

    @pytest.fixture
    def mock_hostname(self) -> Generator[None, None, None]:
        with patch("socket.gethostname", return_value="testhost"):
            yield

    @pytest.fixture
    def aws_provider(self) -> None:
        ai.backend.common.identity.current_provider = CloudProvider.AWS
        ai.backend.common.identity._defined = False
        ai.backend.common.identity._define_functions()
        return

    @pytest.mark.parametrize(
        ("curl_return", "expected"),
        [
            (json.dumps({"region": "us-east-1"}), "amazon/us-east-1"),
            ("not json", "amazon/unknown"),
            (json.dumps({"otherKey": "value"}), "amazon/unknown"),
            ("", "amazon/unknown"),
        ],
        ids=["valid_json", "invalid_json", "missing_key", "empty_response"],
    )
    async def test_get_instance_region(
        self, mock_curl: AsyncMock, aws_provider: None, curl_return: str, expected: str
    ) -> None:
        mock_curl.return_value = curl_return
        result = await ai.backend.common.identity.get_instance_region()
        assert result == expected

    @pytest.fixture
    def azure_provider(self) -> None:
        ai.backend.common.identity.current_provider = CloudProvider.AZURE
        ai.backend.common.identity._defined = False
        ai.backend.common.identity._define_functions()
        return

    async def test_get_instance_id_with_invalid_json(
        self, mock_curl: AsyncMock, mock_hostname: None, azure_provider: None
    ) -> None:
        mock_curl.return_value = "not json"
        result = await ai.backend.common.identity.get_instance_id()
        assert result == "i-testhost"

    @pytest.mark.parametrize(
        ("curl_return", "expected"),
        [
            ("not json", "127.0.0.1"),
            ("", "127.0.0.1"),
        ],
        ids=["invalid_json", "empty_response"],
    )
    async def test_get_instance_ip_fallback(
        self, mock_curl: AsyncMock, azure_provider: None, curl_return: str, expected: str
    ) -> None:
        mock_curl.return_value = curl_return
        result = await ai.backend.common.identity.get_instance_ip(None)
        assert result == expected

    async def test_get_instance_type_with_invalid_json(
        self, mock_curl: AsyncMock, azure_provider: None
    ) -> None:
        mock_curl.return_value = "not json"
        result = await ai.backend.common.identity.get_instance_type()
        assert result == "unknown"

    @pytest.mark.parametrize(
        ("curl_return", "expected"),
        [
            ("not json", "azure/unknown"),
            (json.dumps({"compute": {"otherKey": "val"}}), "azure/unknown"),
        ],
        ids=["invalid_json", "missing_key"],
    )
    async def test_get_instance_region_fallback(
        self, mock_curl: AsyncMock, azure_provider: None, curl_return: str, expected: str
    ) -> None:
        mock_curl.return_value = curl_return
        result = await ai.backend.common.identity.get_instance_region()
        assert result == expected

    @pytest.fixture
    def gcp_provider(self) -> None:
        ai.backend.common.identity.current_provider = CloudProvider.GCP
        ai.backend.common.identity._defined = False
        ai.backend.common.identity._define_functions()
        return

    @pytest.mark.parametrize(
        "curl_return",
        ["not-a-number", ""],
        ids=["non_numeric", "empty"],
    )
    async def test_get_instance_id_fallback(
        self, mock_curl: AsyncMock, mock_hostname: None, gcp_provider: None, curl_return: str
    ) -> None:
        mock_curl.return_value = curl_return
        result = await ai.backend.common.identity.get_instance_id()
        assert result == "i-testhost"
