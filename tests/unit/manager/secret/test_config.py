from __future__ import annotations

import base64
from typing import Any

import pytest

from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.manager.config.unified import ConfigKeyProviderConfig, SecretEncryptionConfig
from ai.backend.manager.data.secret.types import KeyProviderType


def _key(seed: int) -> str:
    return base64.b64encode(bytes([seed]) * 32).decode()


def _provider(**raw: Any) -> ConfigKeyProviderConfig:
    return ConfigKeyProviderConfig.model_validate(raw)


class TestConfigKeyProviderConfig:
    def test_a_section_without_an_active_key_id_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            _provider(keys={"v1": _key(1)})

    def test_a_section_without_keys_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            _provider(**{"active-key-id": "v1"})

    def test_an_active_key_id_outside_the_key_list_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            _provider(**{"active-key-id": "v2", "keys": {"v1": _key(1)}})

    def test_a_key_of_the_wrong_size_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            _provider(**{
                "active-key-id": "v1",
                "keys": {"v1": base64.b64encode(b"short").decode()},
            })

    def test_the_url_safe_alphabet_is_accepted(self) -> None:
        material = base64.urlsafe_b64encode(bytes([0xFB, 0xEF] * 16)).decode()
        assert "-" in material and "_" in material
        assert _provider(**{"active-key-id": "v1", "keys": {"v1": material}}).keys == {
            "v1": material
        }

    def test_a_non_base64_key_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            _provider(**{"active-key-id": "v1", "keys": {"v1": "!!!!"}})

    def test_an_empty_key_id_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            _provider(**{"active-key-id": "", "keys": {"": _key(1)}})


class TestSecretEncryptionConfig:
    def test_an_unknown_write_provider_type_is_rejected(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            SecretEncryptionConfig.model_validate({"write-provider-type": "kms"})

    def test_the_default_writes_plaintext_and_configures_no_provider(self) -> None:
        config = SecretEncryptionConfig.model_validate({})
        assert config.write_provider_type is KeyProviderType.PLAIN
        assert config.config_provider is None

    def test_the_kebab_case_keys_are_accepted(self) -> None:
        config = SecretEncryptionConfig.model_validate({
            "write-provider-type": "config",
            "config-provider": {"active-key-id": "v1", "keys": {"v1": _key(1)}},
        })
        assert config.write_provider_type is KeyProviderType.CONFIG
        assert config.config_provider is not None
        assert config.config_provider.active_key_id == "v1"
        assert config.config_provider.keys == {"v1": _key(1)}
