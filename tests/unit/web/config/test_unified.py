from __future__ import annotations

import pytest

from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.web.config.unified import ServiceConfig


class TestServiceConfigTrustedProxies:
    def test_accepts_addresses_and_ranges(self) -> None:
        config = ServiceConfig.model_validate({"trusted-proxies": ["10.0.0.2", "172.16.0.0/12"]})

        assert config.trusted_proxies == ["10.0.0.2", "172.16.0.0/12"]

    @pytest.mark.parametrize(
        "proxy",
        ["not-an-address", "10.0.0.2/24"],
        ids=["not_an_address", "host_bits_set"],
    )
    def test_rejects_a_malformed_entry(self, proxy: str) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match="Invalid trusted proxy"):
            ServiceConfig.model_validate({"trusted-proxies": [proxy]})
