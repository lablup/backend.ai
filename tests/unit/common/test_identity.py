from __future__ import annotations

import json
from collections.abc import Generator, Mapping
from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import pytest
from yarl import URL

import ai.backend.common.identity
from ai.backend.common.exception import CloudDetectionError
from ai.backend.common.identity import (
    CloudProvider,
    _detect_aws,
    _detect_azure,
    _detect_gcp,
    detect_cloud,
)


def test_is_containerized() -> None:
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


_AWS_URL = "http://169.254.169.254/latest/meta-data/"
_AZURE_URL = "http://169.254.169.254/metadata/instance/compute?api-version=2021-02-01"
_GCP_URL = "http://169.254.169.254/computeMetadata/v1/instance/id"


@dataclass(frozen=True)
class IMDSMock:
    """Mocked IMDS endpoint response specification."""

    body: str = ""
    status: int = 200


class IMDSRoutes:
    """IMDS responses by URL, served through a mocked ``aiohttp.ClientSession``."""

    _routes: dict[str, IMDSMock | BaseException]

    def __init__(self) -> None:
        self._routes = {}

    def add(
        self,
        url: str,
        *,
        status: int = 200,
        body: str = "",
        exception: BaseException | None = None,
    ) -> None:
        self._routes[url] = exception if exception is not None else IMDSMock(body, status)

    def session(self) -> Mock:
        session = Mock()
        session.get = Mock(side_effect=self._respond)
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        return session

    def _respond(
        self, url: str, *, params: Mapping[str, str] | None = None, headers: Any = None
    ) -> Mock:
        key = str(URL(url).update_query(params)) if params else url
        route = self._routes.get(key)
        if route is None:
            raise aiohttp.ClientConnectionError(key)
        if isinstance(route, BaseException):
            raise route
        body = route.body
        resp = Mock(status=route.status)
        resp.text = AsyncMock(return_value=body)
        resp.json = AsyncMock(side_effect=lambda: json.loads(body))
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=None)
        return resp


class TestDetectCloudServices:
    @pytest.fixture
    def mock_responses(self) -> IMDSRoutes:
        return IMDSRoutes()

    @pytest.fixture
    def client_session(self, mock_responses: IMDSRoutes) -> aiohttp.ClientSession:
        return cast(aiohttp.ClientSession, mock_responses.session())

    @pytest.fixture
    def aws_metadata_url(self) -> str:
        return _AWS_URL

    async def test_valid_aws_metadata(
        self,
        mock_responses: IMDSRoutes,
        client_session: aiohttp.ClientSession,
        aws_metadata_url: str,
    ) -> None:
        mock_responses.add(
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
        mock_responses: IMDSRoutes,
        client_session: aiohttp.ClientSession,
        aws_metadata_url: str,
        body: str,
    ) -> None:
        mock_responses.add(aws_metadata_url, body=body)
        with pytest.raises(CloudDetectionError, match="AWS detection failed"):
            await _detect_aws(client_session)

    @pytest.mark.parametrize("status", [404, 500, 503], ids=["404", "500", "503"])
    async def test_rejects_non_200_aws_response(
        self,
        mock_responses: IMDSRoutes,
        client_session: aiohttp.ClientSession,
        aws_metadata_url: str,
        status: int,
    ) -> None:
        mock_responses.add(aws_metadata_url, status=status, body="error")
        with pytest.raises(CloudDetectionError, match=f"AWS detection failed with status {status}"):
            await _detect_aws(client_session)

    @pytest.fixture
    def azure_metadata_url(self) -> str:
        return _AZURE_URL

    async def test_valid_azure_metadata(
        self,
        mock_responses: IMDSRoutes,
        client_session: aiohttp.ClientSession,
        azure_metadata_url: str,
    ) -> None:
        mock_responses.add(
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
        mock_responses: IMDSRoutes,
        client_session: aiohttp.ClientSession,
        azure_metadata_url: str,
        body: str,
    ) -> None:
        mock_responses.add(azure_metadata_url, body=body)
        with pytest.raises(CloudDetectionError, match="Azure detection failed"):
            await _detect_azure(client_session)

    @pytest.mark.parametrize("status", [404, 500, 503], ids=["404", "500", "503"])
    async def test_rejects_non_200_azure_response(
        self,
        mock_responses: IMDSRoutes,
        client_session: aiohttp.ClientSession,
        azure_metadata_url: str,
        status: int,
    ) -> None:
        mock_responses.add(azure_metadata_url, status=status, body="error")
        with pytest.raises(
            CloudDetectionError, match=f"Azure detection failed with status {status}"
        ):
            await _detect_azure(client_session)

    @pytest.fixture
    def gcp_metadata_url(self) -> str:
        return _GCP_URL

    async def test_valid_gcp_metadata(
        self,
        mock_responses: IMDSRoutes,
        client_session: aiohttp.ClientSession,
        gcp_metadata_url: str,
    ) -> None:
        mock_responses.add(gcp_metadata_url, body="1234567890123456")
        result = await _detect_gcp(client_session)
        assert result == CloudProvider.GCP

    @pytest.mark.parametrize(
        "body",
        ["not-a-number", ""],
        ids=["non_numeric", "empty_body"],
    )
    async def test_rejects_non_gcp_response(
        self,
        mock_responses: IMDSRoutes,
        client_session: aiohttp.ClientSession,
        gcp_metadata_url: str,
        body: str,
    ) -> None:
        mock_responses.add(gcp_metadata_url, body=body)
        with pytest.raises(CloudDetectionError, match="GCP detection failed"):
            await _detect_gcp(client_session)

    @pytest.mark.parametrize("status", [404, 500, 503], ids=["404", "500", "503"])
    async def test_rejects_non_200_gcp_response(
        self,
        mock_responses: IMDSRoutes,
        client_session: aiohttp.ClientSession,
        gcp_metadata_url: str,
        status: int,
    ) -> None:
        mock_responses.add(gcp_metadata_url, status=status, body="error")
        with pytest.raises(CloudDetectionError, match=f"GCP detection failed with status {status}"):
            await _detect_gcp(client_session)


@dataclass(frozen=True)
class DetectCloudScenario:
    """Bundled scenario for detect_cloud() parametrized tests."""

    aws: IMDSMock
    azure: IMDSMock
    gcp: IMDSMock
    expected: CloudProvider | None


class TestDetectCloud:
    @pytest.fixture
    def mock_responses(self) -> Generator[IMDSRoutes, None, None]:
        routes = IMDSRoutes()
        with patch(
            "ai.backend.common.identity.aiohttp.ClientSession",
            Mock(return_value=routes.session()),
        ):
            yield routes

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
        mock_responses: IMDSRoutes,
        scenario: DetectCloudScenario,
    ) -> None:
        mock_responses.add(_AWS_URL, status=scenario.aws.status, body=scenario.aws.body)
        mock_responses.add(_AZURE_URL, status=scenario.azure.status, body=scenario.azure.body)
        mock_responses.add(_GCP_URL, status=scenario.gcp.status, body=scenario.gcp.body)
        result = await detect_cloud()
        assert result == scenario.expected

    async def test_detect_cloud_returns_none_on_network_errors(
        self,
        mock_responses: IMDSRoutes,
    ) -> None:
        mock_responses.add(_AWS_URL, exception=aiohttp.ClientConnectionError())
        mock_responses.add(_AZURE_URL, exception=aiohttp.ClientConnectionError())
        mock_responses.add(_GCP_URL, exception=aiohttp.ClientConnectionError())
        result = await detect_cloud()
        assert result is None

    async def test_detect_cloud_picks_valid_when_others_fail(
        self,
        mock_responses: IMDSRoutes,
    ) -> None:
        mock_responses.add(_AWS_URL, body="<html>not aws</html>")
        mock_responses.add(_AZURE_URL, exception=aiohttp.ClientConnectionError())
        mock_responses.add(_GCP_URL, body="1234567890123456")
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
