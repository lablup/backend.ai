from __future__ import annotations

from collections.abc import Callable
from typing import cast
from unittest.mock import MagicMock

import pytest
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes

from ai.backend.common.types import SSHPrivateKey, SSHPublicKey
from ai.backend.manager.errors.keypair import (
    InvalidSSHPrivateKey,
    InvalidSSHPublicKey,
    SSHKeypairMismatch,
)
from ai.backend.manager.models.keypair.ssh_key_validator import (
    PrivateKeyLoader,
    PublicKeyLoader,
    SSHKeyValidator,
)

_Encoding = crypto_serialization.Encoding
_PrivateFormat = crypto_serialization.PrivateFormat
_PublicFormat = crypto_serialization.PublicFormat
_NoEncryption = crypto_serialization.NoEncryption

KeypairFactory = Callable[[], tuple[SSHPrivateKey, SSHPublicKey]]


def _rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def rsa_pem_keypair() -> tuple[SSHPrivateKey, SSHPublicKey]:
    """RSA private key in traditional PEM (OpenSSL) format with an OpenSSH public key."""
    key = _rsa_key()
    private_key = key.private_bytes(
        _Encoding.PEM, _PrivateFormat.TraditionalOpenSSL, _NoEncryption()
    ).decode("utf-8")
    public_key = (
        key.public_key().public_bytes(_Encoding.OpenSSH, _PublicFormat.OpenSSH).decode("utf-8")
    )
    return SSHPrivateKey(private_key), SSHPublicKey(public_key)


def rsa_pkcs8_keypair() -> tuple[SSHPrivateKey, SSHPublicKey]:
    """RSA private key in PKCS#8 PEM format (-----BEGIN PRIVATE KEY-----)."""
    key = _rsa_key()
    private_key = key.private_bytes(_Encoding.PEM, _PrivateFormat.PKCS8, _NoEncryption()).decode(
        "utf-8"
    )
    public_key = (
        key.public_key().public_bytes(_Encoding.OpenSSH, _PublicFormat.OpenSSH).decode("utf-8")
    )
    return SSHPrivateKey(private_key), SSHPublicKey(public_key)


def rsa_openssh_keypair() -> tuple[SSHPrivateKey, SSHPublicKey]:
    """RSA private key in OpenSSH container format (-----BEGIN OPENSSH PRIVATE KEY-----)."""
    key = _rsa_key()
    private_key = key.private_bytes(_Encoding.PEM, _PrivateFormat.OpenSSH, _NoEncryption()).decode(
        "utf-8"
    )
    public_key = (
        key.public_key().public_bytes(_Encoding.OpenSSH, _PublicFormat.OpenSSH).decode("utf-8")
    )
    return SSHPrivateKey(private_key), SSHPublicKey(public_key)


def ed25519_openssh_keypair() -> tuple[SSHPrivateKey, SSHPublicKey]:
    """ed25519 private key in OpenSSH format (produced by `ssh-keygen -t ed25519`)."""
    key = ed25519.Ed25519PrivateKey.generate()
    private_key = key.private_bytes(_Encoding.PEM, _PrivateFormat.OpenSSH, _NoEncryption()).decode(
        "utf-8"
    )
    public_key = (
        key.public_key().public_bytes(_Encoding.OpenSSH, _PublicFormat.OpenSSH).decode("utf-8")
    )
    return SSHPrivateKey(private_key), SSHPublicKey(public_key)


def ecdsa_pem_keypair() -> tuple[SSHPrivateKey, SSHPublicKey]:
    """ECDSA private key in PEM format with an OpenSSH public key."""
    key = ec.generate_private_key(ec.SECP256R1())
    private_key = key.private_bytes(
        _Encoding.PEM, _PrivateFormat.TraditionalOpenSSL, _NoEncryption()
    ).decode("utf-8")
    public_key = (
        key.public_key().public_bytes(_Encoding.OpenSSH, _PublicFormat.OpenSSH).decode("utf-8")
    )
    return SSHPrivateKey(private_key), SSHPublicKey(public_key)


def encrypted_rsa_pem_keypair() -> tuple[SSHPrivateKey, SSHPublicKey]:
    """RSA private key encrypted with a passphrase, in PEM format."""
    key = _rsa_key()
    private_key = key.private_bytes(
        _Encoding.PEM,
        _PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.BestAvailableEncryption(b"passphrase"),
    ).decode("utf-8")
    public_key = (
        key.public_key().public_bytes(_Encoding.OpenSSH, _PublicFormat.OpenSSH).decode("utf-8")
    )
    return SSHPrivateKey(private_key), SSHPublicKey(public_key)


def encrypted_ed25519_openssh_keypair() -> tuple[SSHPrivateKey, SSHPublicKey]:
    """ed25519 private key encrypted with a passphrase, in OpenSSH format."""
    key = ed25519.Ed25519PrivateKey.generate()
    private_key = key.private_bytes(
        _Encoding.PEM,
        _PrivateFormat.OpenSSH,
        crypto_serialization.BestAvailableEncryption(b"passphrase"),
    ).decode("utf-8")
    public_key = (
        key.public_key().public_bytes(_Encoding.OpenSSH, _PublicFormat.OpenSSH).decode("utf-8")
    )
    return SSHPrivateKey(private_key), SSHPublicKey(public_key)


class TestSSHKeyValidatorValidPairs:
    @pytest.mark.parametrize(
        "factory",
        [
            rsa_pem_keypair,
            rsa_pkcs8_keypair,
            rsa_openssh_keypair,
            ed25519_openssh_keypair,
            ecdsa_pem_keypair,
        ],
    )
    def test_matching_keypair_passes(self, factory: KeypairFactory) -> None:
        private_key, public_key = factory()
        # Should not raise.
        SSHKeyValidator().validate(private_key, public_key)


class TestSSHKeyValidatorPrivateKeyFormat:
    def test_garbage_private_key_raises(self) -> None:
        _, public_key = ed25519_openssh_keypair()
        with pytest.raises(InvalidSSHPrivateKey):
            SSHKeyValidator().validate(SSHPrivateKey("not-a-key"), public_key)

    def test_empty_private_key_raises(self) -> None:
        _, public_key = rsa_pem_keypair()
        with pytest.raises(InvalidSSHPrivateKey):
            SSHKeyValidator().validate(SSHPrivateKey(""), public_key)

    @pytest.mark.parametrize(
        "factory",
        [
            encrypted_rsa_pem_keypair,
            encrypted_ed25519_openssh_keypair,
        ],
    )
    def test_encrypted_private_key_raises(self, factory: KeypairFactory) -> None:
        # Password-protected keys raise TypeError in the loaders; map to InvalidSSHPrivateKey.
        private_key, public_key = factory()
        with pytest.raises(InvalidSSHPrivateKey):
            SSHKeyValidator().validate(private_key, public_key)


class TestSSHKeyValidatorPublicKeyFormat:
    def test_garbage_public_key_raises(self) -> None:
        private_key, _ = rsa_pem_keypair()
        with pytest.raises(InvalidSSHPublicKey):
            SSHKeyValidator().validate(private_key, SSHPublicKey("not-a-public-key"))


class TestSSHKeyValidatorInjectedLoaders:
    def test_pem_only_loader_rejects_openssh_private_key(self) -> None:
        private_key, public_key = ed25519_openssh_keypair()
        # The default validator accepts OpenSSH; a PEM-only loader must reject it.
        pem_only_validator = SSHKeyValidator(
            private_key_loaders=(crypto_serialization.load_pem_private_key,),
        )
        with pytest.raises(InvalidSSHPrivateKey):
            pem_only_validator.validate(private_key, public_key)


class TestSSHKeyValidatorMismatch:
    def test_mismatched_same_type_raises(self) -> None:
        private_key, _ = ed25519_openssh_keypair()
        _, other_public = ed25519_openssh_keypair()
        with pytest.raises(SSHKeypairMismatch):
            SSHKeyValidator().validate(private_key, other_public)

    def test_mismatched_key_types_raises(self) -> None:
        private_key, _ = ed25519_openssh_keypair()
        _, rsa_public = rsa_pem_keypair()
        with pytest.raises(SSHKeypairMismatch):
            SSHKeyValidator().validate(private_key, rsa_public)


def _loaders_with_failing_sign(error: Exception) -> tuple[PrivateKeyLoader, PublicKeyLoader]:
    """Loaders returning an RSA keypair whose ``sign()`` raises the given error.

    Used to exercise the case where a loadable private key cannot actually sign
    (e.g. an RSA key too small for the chosen hash/padding) — not reproducible with
    real keys since the loaders enforce a minimum RSA key size.
    """
    mock_private_key = MagicMock(spec=rsa.RSAPrivateKey)
    mock_private_key.sign.side_effect = error
    mock_public_key = MagicMock(spec=rsa.RSAPublicKey)

    loaded_private_key = cast(PrivateKeyTypes, mock_private_key)
    loaded_public_key = cast(PublicKeyTypes, mock_public_key)

    def private_loader(data: bytes, password: bytes | None) -> PrivateKeyTypes:
        return loaded_private_key

    def public_loader(data: bytes) -> PublicKeyTypes:
        return loaded_public_key

    return private_loader, public_loader


class TestSSHKeyValidatorUnusablePrivateKey:
    @pytest.mark.parametrize(
        "error",
        [
            ValueError("key too small for the requested hash"),
            UnsupportedAlgorithm("unsupported"),
        ],
    )
    def test_sign_failure_raises_invalid_private_key(self, error: Exception) -> None:
        private_loader, public_loader = _loaders_with_failing_sign(error)
        validator = SSHKeyValidator(
            private_key_loaders=(private_loader,),
            public_key_loader=public_loader,
        )
        with pytest.raises(InvalidSSHPrivateKey):
            validator.validate(SSHPrivateKey("dummy"), SSHPublicKey("dummy"))
