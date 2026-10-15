from __future__ import annotations

import pytest

from ai.backend.common.configs.redis import RedisConfig, SingleRedisConfig
from ai.backend.common.exception import BackendAISchemaValidationFailed

ADDR = {"host": "127.0.0.1", "port": 6379}


class TestUsernameRequiresPassword:
    def test_username_with_password_is_accepted(self) -> None:
        config = SingleRedisConfig.model_validate({
            "addr": ADDR,
            "username": "agent",
            "password": "pw",
        })
        assert config.username == "agent"

    def test_username_without_password_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match="requires `password`"):
            SingleRedisConfig.model_validate({"addr": ADDR, "username": "agent"})

    def test_username_without_password_is_rejected_in_override_configs(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed, match="requires `password`"):
            RedisConfig.model_validate({
                "addr": ADDR,
                "username": "agent",
                "password": "pw",
                "override-configs": {"stream": {"addr": ADDR, "username": "stream-agent"}},
            })

    def test_username_with_password_is_accepted_in_override_configs(self) -> None:
        config = RedisConfig.model_validate({
            "addr": ADDR,
            "override-configs": {
                "stream": {"addr": ADDR, "username": "stream-agent", "password": "pw"},
            },
        })
        assert config.override_configs is not None
        assert config.override_configs["stream"].username == "stream-agent"
