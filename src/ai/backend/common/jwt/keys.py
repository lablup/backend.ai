"""RSA key management utilities for JWT RS256 signing."""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)


def generate_rsa_key_pair(
    key_size: int = 2048,
) -> tuple[RSAPrivateKey, RSAPublicKey]:
    """
    Generate a new RSA key pair for JWT RS256 signing.

    Args:
        key_size: RSA key size in bits (default: 2048)

    Returns:
        Tuple of (private_key, public_key) RSA key objects
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    public_key = private_key.public_key()
    return private_key, public_key


def load_private_key(path: Path) -> RSAPrivateKey:
    """
    Load a PEM-encoded RSA private key from a file.

    Args:
        path: Path to the PEM-encoded private key file

    Returns:
        RSA private key object
    """
    key_data = path.read_bytes()
    private_key = serialization.load_pem_private_key(key_data, password=None)
    if not isinstance(private_key, RSAPrivateKey):
        raise TypeError(f"Expected RSA private key, got {type(private_key).__name__}")
    return private_key


def load_public_key(path: Path) -> RSAPublicKey:
    """
    Load a PEM-encoded RSA public key from a file.

    Args:
        path: Path to the PEM-encoded public key file

    Returns:
        RSA public key object
    """
    key_data = path.read_bytes()
    public_key = serialization.load_pem_public_key(key_data)
    if not isinstance(public_key, RSAPublicKey):
        raise TypeError(f"Expected RSA public key, got {type(public_key).__name__}")
    return public_key


def private_key_to_pem(key: RSAPrivateKey) -> bytes:
    """
    Serialize an RSA private key to PEM format.

    Args:
        key: RSA private key object

    Returns:
        PEM-encoded private key bytes
    """
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def public_key_to_pem(key: RSAPublicKey) -> bytes:
    """
    Serialize an RSA public key to PEM format.

    Args:
        key: RSA public key object

    Returns:
        PEM-encoded public key bytes
    """
    return key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def _int_to_base64url(value: int) -> str:
    """
    Encode an integer as a base64url string (no padding) for JWK format.

    Args:
        value: Integer value to encode

    Returns:
        Base64url-encoded string
    """
    byte_length = (value.bit_length() + 7) // 8
    value_bytes = value.to_bytes(byte_length, byteorder="big")
    return base64.urlsafe_b64encode(value_bytes).rstrip(b"=").decode("ascii")


def public_key_to_jwk(key: RSAPublicKey, kid: str) -> dict[str, str]:
    """
    Convert an RSA public key to JWK (JSON Web Key) format.

    Args:
        key: RSA public key object
        kid: Key ID to include in the JWK

    Returns:
        Dictionary in JWK format with kty, n, e, kid, use, and alg fields
    """
    public_numbers = key.public_numbers()
    return {
        "kty": "RSA",
        "n": _int_to_base64url(public_numbers.n),
        "e": _int_to_base64url(public_numbers.e),
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
    }
