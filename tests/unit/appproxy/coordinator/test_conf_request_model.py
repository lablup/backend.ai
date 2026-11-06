from __future__ import annotations

import pytest

from ai.backend.appproxy.coordinator.api.types import ConfRequestModel
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestConfRequestModel:
    def test_rejects_a_metadata_address(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ConfRequestModel.model_validate({
                "login_session_token": None,
                "kernel_host": "169.254.169.254",
                "kernel_port": 80,
                "session": {
                    "id": "f5cd34ba-ae53-4537-a813-09f38496443d",
                    "user_uuid": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
                    "group_id": "2de2b969-1d04-48a6-af16-0bc8adb3c831",
                    "access_key": "AKIAIOSFODNN7EXAMPLE",
                    "domain_name": "default",
                },
            })
