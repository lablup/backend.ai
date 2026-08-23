from __future__ import annotations

import pytest

from ai.backend.manager.errors.secret import (
    InvalidEncryptedSecretFormat,
    UnsupportedSecretFormatVersion,
)
from ai.backend.manager.secret.types import (
    SECRET_MAGIC,
    EncryptedData,
    SecretFormatVersion,
    SecretValue,
    WrappedDataEncryptionKey,
)

LEGACY_PLAINTEXT = "AKIAIOSFODNN7EXAMPLEKEYSECRET0123456789ab"
PROVIDER_ID = "config"
KEY_ID = "v2"
WRAPPED_BLOB = bytes(range(60))
NONCE = bytes(range(12))
CIPHERTEXT = bytes(range(56))


def _encrypted(provider_id: str = PROVIDER_ID, key_id: str = KEY_ID) -> EncryptedData:
    return EncryptedData(
        provider_id=provider_id,
        wrapped_key=WrappedDataEncryptionKey(key_id=key_id, blob=WRAPPED_BLOB),
        nonce=NONCE,
        ciphertext=CIPHERTEXT,
    )


class TestFieldValidation:
    def test_an_empty_key_id_is_rejected(self) -> None:
        with pytest.raises(InvalidEncryptedSecretFormat):
            WrappedDataEncryptionKey(key_id="", blob=WRAPPED_BLOB)

    def test_an_empty_wrapped_key_is_rejected(self) -> None:
        with pytest.raises(InvalidEncryptedSecretFormat):
            WrappedDataEncryptionKey(key_id=KEY_ID, blob=b"")

    def test_an_empty_provider_id_is_rejected(self) -> None:
        with pytest.raises(InvalidEncryptedSecretFormat):
            _encrypted(provider_id="")

    def test_a_provider_id_containing_the_delimiter_is_rejected(self) -> None:
        with pytest.raises(InvalidEncryptedSecretFormat):
            _encrypted(provider_id="con:fig")

    def test_an_empty_nonce_is_rejected(self) -> None:
        with pytest.raises(InvalidEncryptedSecretFormat):
            EncryptedData(
                provider_id=PROVIDER_ID,
                wrapped_key=WrappedDataEncryptionKey(key_id=KEY_ID, blob=WRAPPED_BLOB),
                nonce=b"",
                ciphertext=CIPHERTEXT,
            )

    def test_an_empty_ciphertext_is_rejected(self) -> None:
        with pytest.raises(InvalidEncryptedSecretFormat):
            EncryptedData(
                provider_id=PROVIDER_ID,
                wrapped_key=WrappedDataEncryptionKey(key_id=KEY_ID, blob=WRAPPED_BLOB),
                nonce=NONCE,
                ciphertext=b"",
            )

    def test_the_secret_bytes_are_not_exposed_by_repr(self) -> None:
        value = SecretValue(_encrypted())
        rendered = f"{value!r} {value.content!r}"
        assert WRAPPED_BLOB.hex() not in rendered
        assert CIPHERTEXT.hex() not in rendered
        assert LEGACY_PLAINTEXT not in repr(SecretValue(LEGACY_PLAINTEXT))


class TestPlaintext:
    def test_a_value_without_the_marker_is_read_as_plaintext(self) -> None:
        parsed = SecretValue.parse(LEGACY_PLAINTEXT)
        assert not isinstance(parsed.content, EncryptedData)
        assert parsed.content == LEGACY_PLAINTEXT

    def test_a_plaintext_value_serializes_as_is(self) -> None:
        assert SecretValue(LEGACY_PLAINTEXT).serialize() == LEGACY_PLAINTEXT

    def test_a_plaintext_value_may_not_impersonate_the_marker(self) -> None:
        with pytest.raises(InvalidEncryptedSecretFormat):
            SecretValue(f"{SECRET_MAGIC}:1:config:v1:AAAA:BBBB:CCCC")


class TestRoundTrip:
    def test_an_encrypted_value_round_trips(self) -> None:
        value = SecretValue(_encrypted())
        assert SecretValue.parse(value.serialize()) == value

    def test_the_stored_value_names_the_marker_version_provider_and_key(self) -> None:
        assert (
            SecretValue(_encrypted())
            .serialize()
            .startswith(f"{SECRET_MAGIC}:{SecretFormatVersion.current()}:{PROVIDER_ID}:{KEY_ID}:")
        )

    def test_a_key_id_containing_the_delimiter_round_trips(self) -> None:
        key_id = "projects/p/locations/l:cryptoKeys/k"
        parsed = SecretValue.parse(SecretValue(_encrypted(key_id=key_id)).serialize())
        assert isinstance(parsed.content, EncryptedData)
        assert parsed.content.wrapped_key.key_id == key_id

    def test_the_wrapped_key_and_data_survive_the_round_trip(self) -> None:
        parsed = SecretValue.parse(SecretValue(_encrypted()).serialize())
        assert isinstance(parsed.content, EncryptedData)
        assert parsed.content.wrapped_key.blob == WRAPPED_BLOB
        assert parsed.content.nonce == NONCE
        assert parsed.content.ciphertext == CIPHERTEXT

    def test_serializing_a_parsed_value_reproduces_the_stored_string(self) -> None:
        stored = SecretValue(_encrypted()).serialize()
        assert SecretValue.parse(stored).serialize() == stored
        assert SecretValue.parse(LEGACY_PLAINTEXT).serialize() == LEGACY_PLAINTEXT


class TestMalformed:
    @pytest.mark.parametrize("stored", [f"{SECRET_MAGIC}:", f"{SECRET_MAGIC}:1"])
    def test_a_frame_without_a_body_raises(self, stored: str) -> None:
        with pytest.raises(InvalidEncryptedSecretFormat):
            SecretValue.parse(stored)

    @pytest.mark.parametrize(
        "body",
        [
            "config",
            "config:v1",
            "config:v1:AAAA",
            "config:v1:AAAA:BBBB",
            ":v1:AAAA:BBBB:CCCC",
            "config::AAAA:BBBB:CCCC",
            "config:v1:!!!!:BBBB:CCCC",
        ],
    )
    def test_a_malformed_body_raises(self, body: str) -> None:
        with pytest.raises(InvalidEncryptedSecretFormat):
            SecretValue.parse(f"{SECRET_MAGIC}:{SecretFormatVersion.current()}:{body}")

    @pytest.mark.parametrize("version", ["2", "0", "x", ""])
    def test_an_unreadable_format_version_raises(self, version: str) -> None:
        body = _encrypted().serialize()
        with pytest.raises(UnsupportedSecretFormatVersion):
            SecretValue.parse(f"{SECRET_MAGIC}:{version}:{body}")
