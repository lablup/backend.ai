from __future__ import annotations

import ipaddress
import os
import ssl
from datetime import UTC, datetime, timedelta

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from ai.backend.client.config import APIConfig, set_config


@pytest.fixture
def self_signed_tls_context(tmp_path_factory: pytest.TempPathFactory) -> ssl.SSLContext:
    private_key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )
    pem_dir = tmp_path_factory.mktemp("self-signed-tls")
    certificate_path = pem_dir / "certificate.pem"
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    private_key_path = pem_dir / "private-key.pem"
    private_key_path.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls_context.load_cert_chain(certificate_path, private_key_path)
    return tls_context


@pytest.fixture(autouse=True)
def defconfig() -> APIConfig:
    endpoint = os.environ.get("BACKEND_TEST_ENDPOINT", "http://127.0.0.1:8081")
    access_key = os.environ.get("BACKEND_TEST_ADMIN_ACCESS_KEY", "AKIAIOSFODNN7EXAMPLE")
    secret_key = os.environ.get(
        "BACKEND_TEST_ADMIN_SECRET_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )
    c = APIConfig(endpoint=endpoint, access_key=access_key, secret_key=secret_key)
    set_config(c)
    return c


@pytest.fixture
def userconfig() -> APIConfig:
    endpoint = os.environ.get("BACKEND_TEST_ENDPOINT", "http://127.0.0.1:8081")
    access_key = os.environ.get("BACKEND_TEST_USER_ACCESS_KEY", "AKIANABBDUSEREXAMPLE")
    secret_key = os.environ.get(
        "BACKEND_TEST_USER_SECRET_KEY", "C8qnIo29EZvXkPK_MXcuAakYTy4NYrxwmCEyNPlf"
    )
    c = APIConfig(endpoint=endpoint, access_key=access_key, secret_key=secret_key)
    set_config(c)
    return c


@pytest.fixture
def example_keypair(defconfig: APIConfig) -> tuple[str, str]:
    return (defconfig.access_key, defconfig.secret_key)


@pytest.fixture
def user_keypair(userconfig: APIConfig) -> tuple[str, str]:
    return (userconfig.access_key, userconfig.secret_key)
