import pytest
from pydantic import ValidationError

from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.network.types import NetworkBackendKind
from ai.backend.common.typed_validators import HostPortPair
from ai.backend.manager.config.unified import (
    InterContainerNetworkConfig,
    ManagerConfig,
    MetricConfig,
)

CONFIG_LOGGER = "ai.backend.common.config"


def test_config_validation_supports_field_name_and_alias() -> None:
    config = MetricConfig.model_validate({"address": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)

    config = MetricConfig.model_validate({"addr": "127.0.0.1:9090"}, by_name=True)
    assert config.address == HostPortPair(host="127.0.0.1", port=9090)


def test_inter_container_network_config_is_typed_and_serializes_canonical_keys() -> None:
    config = InterContainerNetworkConfig.model_validate({
        "forced-backend": "vxlan",
        "ipam-pool": "10.144.0.0/16",
        "ipam-block-size": 24,
    })

    assert config.forced_backend is NetworkBackendKind.VXLAN
    assert config.model_dump(by_alias=True)["ipam-pool"] == "10.144.0.0/16"


@pytest.mark.parametrize(
    "raw",
    [
        {"forced-backend": "bridge"},
        {"ipam-pool": "8.8.8.0/24"},
        {"ipam-pool": "10.144.0.1/16"},
        {"ipam-pool": "10.144.0.0/24", "ipam-block-size": 16},
    ],
)
def test_inter_container_network_config_rejects_unusable_values(raw: dict[str, object]) -> None:
    with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
        InterContainerNetworkConfig.model_validate(raw)


def _unknown_field_warnings(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == CONFIG_LOGGER]


class TestUnknownFieldWarning:
    @pytest.mark.parametrize(
        "unknown_key",
        ["use-experimental-redis-event-dispatcher", "totally-made-up-key"],
    )
    def test_unknown_field_is_warned_and_kept(
        self,
        unknown_key: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        with caplog.at_level("WARNING", logger=CONFIG_LOGGER):
            config = ManagerConfig.model_validate({unknown_key: True}, by_name=True)

        warnings = _unknown_field_warnings(caplog)
        assert any(unknown_key in m and "ManagerConfig" in m for m in warnings)
        assert config.model_dump()[unknown_key] is True
        assert unknown_key in config.model_fields_set

    def test_known_field_emits_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level("WARNING", logger=CONFIG_LOGGER):
            config = ManagerConfig.model_validate({"num-proc": 2}, by_name=True)

        assert _unknown_field_warnings(caplog) == []
        assert config.num_proc == 2
