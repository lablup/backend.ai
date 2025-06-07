from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.config.unified import MetricConfig


def test_config_validation_supports_field_name_and_alias() -> None:
    config = MetricConfig.model_validate({"address": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)

    config = MetricConfig.model_validate({"addr": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)
