from __future__ import annotations

import yarl


class DummyApiConfig:
    """Stand-in for the SDK ``APIConfig`` used across webserver unit tests."""

    def __init__(
        self,
        *,
        endpoint: list[yarl.URL],
        domain: str = "default",
        ssl_verify: bool = False,
    ) -> None:
        self.domain = domain
        self.endpoint = endpoint
        self.ssl_verify = ssl_verify


class DummyConfig:
    def __init__(self, api: DummyApiConfig) -> None:
        self.api = api
