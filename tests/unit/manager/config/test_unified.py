import pytest
from pydantic import ValidationError

from ai.backend.common.exception import BackendAISchemaValidationFailed
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
            {"forced_backend": "vxlan"}, by_name=True
        )
        assert config.forced_backend == "vxlan"

    def test_forced_bridge_is_rejected_under_cni_driver(self) -> None:
        # 'bridge' is node-local (single-node) and cannot serve a multi-node cluster session, so it
        # is meaningless as a pin — rejected at startup (not at first session) when cni is in use.
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)) as exc_info:
            InterContainerNetworkConfig.model_validate(
                {"default-driver": "cni", "forced-backend": "bridge"}, by_name=True
            )
        assert "forced-backend 'bridge' is not allowed" in str(exc_info.value)

    def test_forced_unknown_backend_is_rejected_under_cni_driver(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)) as exc_info:
            InterContainerNetworkConfig.model_validate(
                {"default-driver": "cni", "forced-backend": "wireguard"}, by_name=True
            )
        assert "not a valid cluster-network backend" in str(exc_info.value)

    def test_forced_backend_not_validated_under_overlay_driver(self) -> None:
        # forced-backend only applies under the 'cni' driver; the 'overlay' driver (the default)
        # ignores it, so a stale/legacy value must not fail manager startup there.
        config = InterContainerNetworkConfig.model_validate(
            {"default-driver": "overlay", "forced-backend": "wireguard"}, by_name=True
        )
        assert config.forced_backend == "wireguard"
