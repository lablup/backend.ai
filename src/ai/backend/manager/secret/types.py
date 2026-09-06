"""
The stored form of a secret column.

Stored format version 1::

    bai-enc:1:<provider id>:<key id>:<wrapped key>:<nonce>:<ciphertext>

The three trailing fields are base64url. A value without the ``bai-enc:`` marker is
legacy plaintext.
"""

from __future__ import annotations

import base64
import binascii
import enum
from dataclasses import dataclass, field
from typing import Final, Self

from ai.backend.manager.data.secret.types import KeyProviderType, SecretKeyId
from ai.backend.manager.errors.secret import (
    InvalidEncryptedSecretFormat,
    UnknownSecretKeyProvider,
    UnsupportedSecretFormatVersion,
)

SECRET_MAGIC: Final[str] = "bai-enc"
SECRET_FIELD_DELIMITER: Final[str] = ":"

# A legacy secret key is `secrets.token_urlsafe` output, whose alphabet excludes the
# delimiter, so a legacy value can never begin with this marker.
_MARKER: Final[str] = f"{SECRET_MAGIC}{SECRET_FIELD_DELIMITER}"
_FRAME_FIELD_COUNT: Final[int] = 3
_TRAILING_FIELD_COUNT: Final[int] = 3


class SecretFormatVersion(enum.StrEnum):
    """Stored format versions this build can read. A new version is added, not swapped in."""

    V1 = "1"

    @classmethod
    def current(cls) -> SecretFormatVersion:
        """The version new values are written in."""
        return cls.V1


@dataclass(frozen=True)
class WrappedDataEncryptionKey:
    """The data encryption key as stored. Both fields are set and read by its provider."""

    key_id: SecretKeyId
    blob: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if not self.key_id:
            raise InvalidEncryptedSecretFormat("The key id of a wrapped secret key is empty.")
        if not self.blob:
            raise InvalidEncryptedSecretFormat("The wrapped secret key is empty.")


@dataclass(frozen=True)
class EncryptedData:
    """A secret in its encrypted form, addressed to the key provider that wrote it."""

    provider_type: KeyProviderType
    wrapped_key: WrappedDataEncryptionKey
    nonce: bytes = field(repr=False)
    ciphertext: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if self.provider_type is KeyProviderType.PLAIN:
            raise InvalidEncryptedSecretFormat(
                "A plaintext secret is stored without a marker, so it cannot name a provider."
            )
        if not self.nonce:
            raise InvalidEncryptedSecretFormat("An encrypted secret carries an empty nonce.")
        if not self.ciphertext:
            raise InvalidEncryptedSecretFormat("An encrypted secret carries an empty ciphertext.")

    @classmethod
    def parse(cls, body: str) -> Self:
        provider_type, _, tail = body.partition(SECRET_FIELD_DELIMITER)
        # The key id is provider-defined and may contain the delimiter, so the three
        # base64url fields after it are split off from the right.
        fields = tail.rsplit(SECRET_FIELD_DELIMITER, _TRAILING_FIELD_COUNT)
        if len(fields) != _TRAILING_FIELD_COUNT + 1:
            raise InvalidEncryptedSecretFormat(
                "An encrypted secret must hold a key provider type, a key id, "
                "a wrapped key, a nonce, and a ciphertext."
            )
        key_id, encoded_key, encoded_nonce, encoded_ciphertext = fields
        return cls(
            provider_type=cls._provider_type(provider_type),
            wrapped_key=WrappedDataEncryptionKey(
                key_id=SecretKeyId(key_id), blob=cls._decode(encoded_key)
            ),
            nonce=cls._decode(encoded_nonce),
            ciphertext=cls._decode(encoded_ciphertext),
        )

    def serialize(self) -> str:
        return SECRET_FIELD_DELIMITER.join([
            self.provider_type,
            self.wrapped_key.key_id,
            self._encode(self.wrapped_key.blob),
            self._encode(self.nonce),
            self._encode(self.ciphertext),
        ])

    @classmethod
    def _provider_type(cls, raw: str) -> KeyProviderType:
        try:
            return KeyProviderType(raw)
        except ValueError as e:
            raise UnknownSecretKeyProvider(
                f"The stored secret names the key provider {raw!r}, which this build does not know."
            ) from e

    @classmethod
    def _decode(cls, encoded: str) -> bytes:
        try:
            return base64.b64decode(encoded, altchars=b"-_", validate=True)
        except (binascii.Error, ValueError) as e:
            raise InvalidEncryptedSecretFormat(
                "Failed to decode a base64 field of an encrypted secret."
            ) from e

    def _encode(self, raw: bytes) -> str:
        return base64.urlsafe_b64encode(raw).decode("ascii")


@dataclass(frozen=True)
class SecretValue:
    """What a secret column holds: legacy plaintext, or a value some provider encrypted."""

    content: str | EncryptedData = field(repr=False)

    def __post_init__(self) -> None:
        if isinstance(self.content, str) and self.content.startswith(_MARKER):
            raise InvalidEncryptedSecretFormat(
                "A plaintext secret must not begin with the encrypted secret marker."
            )

    @classmethod
    def parse(cls, stored: str) -> Self:
        if not stored.startswith(_MARKER):
            return cls(stored)
        fields = stored.split(SECRET_FIELD_DELIMITER, _FRAME_FIELD_COUNT - 1)
        if len(fields) != _FRAME_FIELD_COUNT:
            raise InvalidEncryptedSecretFormat(
                "An encrypted secret must hold a marker, a format version, and a body."
            )
        _, version, body = fields
        # One arm per readable format version: a new version adds an arm, it does not
        # replace this one, so values written by older builds keep parsing.
        match version:
            case SecretFormatVersion.V1:
                return cls(EncryptedData.parse(body))
            case _:
                raise UnsupportedSecretFormatVersion(
                    f"The stored secret is in format version {version!r}, "
                    "which this build cannot read."
                )

    def serialize(self) -> str:
        match self.content:
            case EncryptedData() as data:
                return SECRET_FIELD_DELIMITER.join([
                    SECRET_MAGIC,
                    SecretFormatVersion.current(),
                    data.serialize(),
                ])
            case _:
                return self.content
