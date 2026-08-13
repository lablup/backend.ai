import pytest
from pydantic import ValidationError

from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.config.unified import ManagerConfig, MetricConfig


def test_config_validation_supports_field_name_and_alias() -> None:
    config = MetricConfig.model_validate({"address": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)

    config = MetricConfig.model_validate({"addr": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)


class TestRemovedExperimentalRedisEventDispatcher:
    @pytest.mark.parametrize(
        "alias",
        ["use-experimental-redis-event-dispatcher", "use_experimental_redis_event_dispatcher"],
    )
    def test_enabled_flag_is_rejected(self, alias: str) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)) as exc_info:
            ManagerConfig.model_validate({alias: True}, by_name=True)

        assert f"The '{alias}' option has been removed." in str(exc_info.value)

    def test_disabled_flag_is_ignored(self) -> None:
        config = ManagerConfig.model_validate(
            {"use-experimental-redis-event-dispatcher": False}, by_name=True
        )

        assert not hasattr(config, "use_experimental_redis_event_dispatcher")
