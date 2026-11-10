"""The stored secret operations as the v2 GraphQL schema exposes them."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.secret.response import (
    AdminSecretStatusPayload,
    SecretKeyCount,
)
from ai.backend.manager.api.gql.schema import schema
from ai.backend.manager.api.gql.secret.types import AdminSecretStatusPayloadGQL


class TestSchemaRegistration:
    def test_the_root_fields_are_present(self) -> None:
        sdl = schema.as_str()
        assert "adminReencryptSecrets:" in sdl
        assert "adminSecretStatus:" in sdl
        assert "type AdminSecretStatusPayload " in sdl
        assert "type SecretKeyCount " in sdl


class TestPayload:
    def test_the_status_payload_carries_one_row_per_column_and_key(self) -> None:
        payload = AdminSecretStatusPayloadGQL.from_pydantic(
            AdminSecretStatusPayload(
                write_provider_type="config",
                counts=[
                    SecretKeyCount(
                        column="keypairs.secret_key",
                        provider_type="config",
                        key_id="v1",
                        count=2,
                    ),
                    SecretKeyCount(
                        column="keypairs.secret_key",
                        provider_type="plain",
                        key_id=None,
                        count=1,
                    ),
                ],
            )
        )

        assert payload.write_provider_type == "config"
        assert [(count.key_id, count.count) for count in payload.counts] == [("v1", 2), (None, 1)]
