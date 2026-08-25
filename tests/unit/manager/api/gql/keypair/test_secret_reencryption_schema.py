"""The secret re-encryption surfaces as the v2 GraphQL schema exposes them."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminKeypairSecretStatusPayload,
    KeypairSecretKeyCount,
)
from ai.backend.manager.api.gql.keypair.types import AdminKeypairSecretStatusPayloadGQL
from ai.backend.manager.api.gql.schema import schema


class TestSchemaRegistration:
    def test_the_root_fields_are_present(self) -> None:
        sdl = schema.as_str()
        assert "adminReencryptKeypairSecrets:" in sdl
        assert "adminKeypairSecretStatusV2:" in sdl
        assert "type AdminKeypairSecretStatusPayload " in sdl
        assert "type KeypairSecretKeyCount " in sdl


class TestPayload:
    def test_the_status_payload_carries_one_row_per_key(self) -> None:
        payload = AdminKeypairSecretStatusPayloadGQL.from_pydantic(
            AdminKeypairSecretStatusPayload(
                write_provider_type="config",
                counts=[
                    KeypairSecretKeyCount(provider_type="config", key_id="v1", count=2),
                    KeypairSecretKeyCount(provider_type="plain", key_id=None, count=1),
                ],
            )
        )

        assert payload.write_provider_type == "config"
        assert [(count.key_id, count.count) for count in payload.counts] == [("v1", 2), (None, 1)]
