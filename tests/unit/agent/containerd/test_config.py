from __future__ import annotations

from ai.backend.agent.config.unified import ContainerdConfig


class TestContainerdConfig:
    def test_defaults_are_empty(self) -> None:
        config = ContainerdConfig.model_validate({})

        assert config.runtime_profiles == []
        assert config.profile_required_slots == []
        assert config.profiles == {}

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
