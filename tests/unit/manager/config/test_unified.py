from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.config.unified import InterContainerNetworkConfig, MetricConfig


def test_config_validation_supports_field_name_and_alias() -> None:
    config = MetricConfig.model_validate({"address": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)

    config = MetricConfig.model_validate({"addr": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)


class TestInterContainerNetworkConfig:
    def test_forced_backend_defaults_to_none(self) -> None:
        config = InterContainerNetworkConfig.model_validate({}, by_name=True)
        assert config.forced_backend is None

    def test_forced_backend_accepts_hyphen_alias(self) -> None:
        config = InterContainerNetworkConfig.model_validate(
            {"forced-backend": "vxlan"}, by_name=True
        )
        assert config.forced_backend == "vxlan"

    def test_forced_backend_accepts_field_name(self) -> None:
        config = InterContainerNetworkConfig.model_validate(
            {"forced_backend": "host-gw"}, by_name=True
        )
        assert config.forced_backend == "host-gw"
