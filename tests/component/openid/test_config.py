"""Tests for the OpenID provider client credential validation."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.manager.plugin.openid.config import OpenIDProviderConfig

from .conftest import ClientCertificate


class TestOpenIDProviderClientCredential:
    @pytest.fixture
    def base_config(self) -> dict[str, Any]:
        return {"client_id": "test-client-id"}

    def test_client_secret_only(self, base_config: dict[str, Any]) -> None:
        config = OpenIDProviderConfig(**base_config, client_secret="secret")

        assert config.client_secret == "secret"
        assert config.private_key is None

    def test_private_key_with_certificate(
        self, base_config: dict[str, Any], client_certificate: ClientCertificate
    ) -> None:
        config = OpenIDProviderConfig(
            **base_config,
            private_key=client_certificate.private_key,
            certificate=client_certificate.certificate,
        )

        assert config.client_secret is None
        assert config.client_assertion_alg == "PS256"

    def test_both_credentials_rejected(
        self, base_config: dict[str, Any], client_certificate: ClientCertificate
    ) -> None:
        with pytest.raises(ValidationError):
            OpenIDProviderConfig(
                **base_config,
                client_secret="secret",
                private_key=client_certificate.private_key,
                certificate=client_certificate.certificate,
            )

    def test_no_credential_rejected(self, base_config: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            OpenIDProviderConfig(**base_config)

    def test_private_key_without_certificate_rejected(
        self, base_config: dict[str, Any], client_certificate: ClientCertificate
    ) -> None:
        with pytest.raises(ValidationError):
            OpenIDProviderConfig(**base_config, private_key=client_certificate.private_key)
