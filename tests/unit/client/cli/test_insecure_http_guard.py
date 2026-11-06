from __future__ import annotations

from dataclasses import dataclass

import click
import pytest
from yarl import URL

from ai.backend.client.cli.insecure_http_guard import reject_insecure_secret_endpoints


@dataclass(frozen=True)
class _AcceptedEndpointsCase:
    endpoints: list[str]
    allow_insecure_http: bool


@dataclass(frozen=True)
class _RejectedEndpointsCase:
    endpoints: list[str]
    expected_refused_endpoints: str


class TestRejectInsecureSecretEndpoints:
    @pytest.mark.parametrize(
        "case",
        [
            _AcceptedEndpointsCase(["https://backend.example"], allow_insecure_http=False),
            _AcceptedEndpointsCase(["http://localhost:8090"], allow_insecure_http=False),
            _AcceptedEndpointsCase(["http://127.0.0.1:8090"], allow_insecure_http=False),
            _AcceptedEndpointsCase(["http://127.1.2.3:8090"], allow_insecure_http=False),
            _AcceptedEndpointsCase(["http://[::1]:8090"], allow_insecure_http=False),
            _AcceptedEndpointsCase(
                ["https://backend.example", "http://127.0.0.1:8090"],
                allow_insecure_http=False,
            ),
            _AcceptedEndpointsCase(["http://backend.example"], allow_insecure_http=True),
        ],
        ids=lambda case: f"{','.join(case.endpoints)}-allow={case.allow_insecure_http}",
    )
    def test_accepts_endpoint_that_keeps_the_secret_private_or_is_allowed(
        self,
        case: _AcceptedEndpointsCase,
    ) -> None:
        reject_insecure_secret_endpoints(
            [URL(endpoint) for endpoint in case.endpoints],
            case.allow_insecure_http,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _RejectedEndpointsCase(
                endpoints=["http://backend.example"],
                expected_refused_endpoints="http://backend.example",
            ),
            _RejectedEndpointsCase(
                endpoints=["http://10.0.0.1:8090"],
                expected_refused_endpoints="http://10.0.0.1:8090",
            ),
            _RejectedEndpointsCase(
                endpoints=["http://localhost.example"],
                expected_refused_endpoints="http://localhost.example",
            ),
            _RejectedEndpointsCase(
                endpoints=[
                    "https://safe.example",
                    "http://first.example",
                    "http://second.example",
                ],
                expected_refused_endpoints="http://first.example, http://second.example",
            ),
        ],
        ids=lambda case: ",".join(case.endpoints),
    )
    def test_rejects_naming_only_the_insecure_endpoints(
        self,
        case: _RejectedEndpointsCase,
    ) -> None:
        with pytest.raises(click.ClickException) as raised:
            reject_insecure_secret_endpoints(
                [URL(endpoint) for endpoint in case.endpoints],
                allow_insecure_http=False,
            )

        assert f"to {case.expected_refused_endpoints}:" in raised.value.message
