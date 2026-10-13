from __future__ import annotations

from ipaddress import IPv4Network

import pytest

from ai.backend.agent.config.unified import ContainerdConfig
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestContainerdConfig:
    def test_defaults_are_empty(self) -> None:
        config = ContainerdConfig.model_validate({})

        assert config.runtime_profiles == []
        assert config.profile_required_slots == []
        assert config.profiles == {}

    def test_connection_defaults(self) -> None:
        config = ContainerdConfig.model_validate({})

        assert config.address == "/run/containerd/containerd.sock"
        assert config.namespace == "backend-ai"
        assert config.snapshotter == "overlayfs"

    def test_connection_overrides(self) -> None:
        config = ContainerdConfig.model_validate({
            "address": "/run/k3s/containerd/containerd.sock",
            "namespace": "k8s.io",
            "snapshotter": "native",
        })

        assert config.address == "/run/k3s/containerd/containerd.sock"
        assert config.namespace == "k8s.io"
        assert config.snapshotter == "native"

    def test_kebab_keys(self) -> None:
        config = ContainerdConfig.model_validate({
            "runtime-profiles": ["coco-tdx"],
            "profile-required-slots": ["confidential.tdx"],
        })

        assert config.runtime_profiles == ["coco-tdx"]
        assert config.profile_required_slots == ["confidential.tdx"]

    def test_snake_keys(self) -> None:
        config = ContainerdConfig.model_validate({
            "runtime_profiles": ["coco-tdx"],
            "profile_required_slots": ["confidential.tdx"],
        })

        assert config.runtime_profiles == ["coco-tdx"]
        assert config.profile_required_slots == ["confidential.tdx"]

    def test_profiles_nested_table_is_preserved(self) -> None:
        table = {"coco-tdx": {"standin-image": "ref", "nested": {"k": 1}}}

        config = ContainerdConfig.model_validate({"profiles": table})

        assert config.profiles == table

    def test_bridge_defaults(self) -> None:
        config = ContainerdConfig.model_validate({})

        assert config.bridge_name == "bai0"
        assert config.bridge_subnet == IPv4Network("172.30.0.0/24")

    @pytest.mark.parametrize("key", ["bridge-name", "bridge_name"])
    def test_bridge_name_aliases(self, key: str) -> None:
        assert ContainerdConfig.model_validate({key: "bai-x"}).bridge_name == "bai-x"

    @pytest.mark.parametrize("key", ["bridge-subnet", "bridge_subnet"])
    def test_bridge_subnet_aliases(self, key: str) -> None:
        config = ContainerdConfig.model_validate({key: "172.30.3.0/24"})

        assert config.bridge_subnet == IPv4Network("172.30.3.0/24")

    @pytest.mark.parametrize("name", ["", "a" * 16, "-bai", "bai_0", "bai 0"])
    def test_bridge_name_is_rejected(self, name: str) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ContainerdConfig.model_validate({"bridge-name": name})

    def test_bridge_name_of_15_chars_is_accepted(self) -> None:
        assert ContainerdConfig.model_validate({"bridge-name": "a" * 15}).bridge_name == "a" * 15

    @pytest.mark.parametrize("subnet", ["172.30.0.0/31", "172.30.0.0/32"])
    def test_bridge_subnet_prefix_over_30_is_rejected(self, subnet: str) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ContainerdConfig.model_validate({"bridge-subnet": subnet})

    def test_bridge_subnet_prefix_30_is_accepted(self) -> None:
        assert ContainerdConfig.model_validate({"bridge-subnet": "10.0.0.0/30"}).bridge_subnet == (
            IPv4Network("10.0.0.0/30")
        )
