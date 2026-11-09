from __future__ import annotations

from typing import Any

import pytest

from ai.backend.appproxy.coordinator.api.proxy import AddRequestModel
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestAllowedClientIPs:
    @pytest.fixture
    def base_params(self) -> dict[str, Any]:
        return {"app": "jupyter", "protocol": "http", "open_to_public": True}

    @pytest.mark.parametrize(
        "value",
        [
            None,
            "",
            "10.0.0.1",
            "10.0.0.0/8, 192.168.1.5",
            "2001:db8::/32",
            "10.0.0.1/24",
            "10.0.0.1,,",
        ],
    )
    def test_accepts_ip_and_cidr(self, base_params: dict[str, Any], value: str | None) -> None:
        params = AddRequestModel.model_validate({**base_params, "allowed_client_ips": value})
        assert params.allowed_client_ips == value

    @pytest.mark.parametrize(
        "value",
        [
            "8001",
            "example.com",
            "10.0.0.1, example.com",
            "10.0.0.0/33",
        ],
    )
    def test_rejects_non_ip_entry(self, base_params: dict[str, Any], value: str) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            AddRequestModel.model_validate({**base_params, "allowed_client_ips": value})

    def test_rejects_value_longer_than_column(self, base_params: dict[str, Any]) -> None:
        value = ",".join(["10.0.0.1"] * 40)
        with pytest.raises(BackendAISchemaValidationFailed):
            AddRequestModel.model_validate({**base_params, "allowed_client_ips": value})
