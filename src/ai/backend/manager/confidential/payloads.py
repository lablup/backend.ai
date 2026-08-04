from __future__ import annotations

import hashlib
import io
import json
import secrets
import tarfile
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from ai.backend.common.types import ClusterSSHKeyPair

TIME_RESOURCE: Final = "default/backendai/time"
CHANNEL_LIFETIME: Final = timedelta(days=7)
CHANNEL_CLOCK_SKEW: Final = timedelta(minutes=5)


@dataclass(frozen=True)
class ChannelIdentity:
    bundle: bytes
    fingerprint: str
    token: str
    expires_at: datetime


def _archive(entries: Mapping[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as bundle:
        for name, payload in entries.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            bundle.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def configuration_bundle(environ: Mapping[str, str]) -> bytes:
    written = "".join(f"{key}={value}\n" for key, value in environ.items()).encode("utf-8")
    return _archive({"environ.txt": written, "environ_base.txt": written})


def secrets_bundle(
    ssh_keypair: ClusterSSHKeyPair | None, internal_data: Mapping[str, Any]
) -> bytes | None:
    entries: dict[str, bytes] = {}
    if ssh_keypair is not None:
        entries["ssh/authorized_keys"] = ssh_keypair["public_key"].encode("utf-8")
        entries["ssh/id_rsa"] = ssh_keypair["private_key"].encode("utf-8")
    credentials = internal_data.get("docker_credentials")
    if credentials:
        entries["docker-creds.json"] = json.dumps(credentials).encode("utf-8")
    return _archive(entries) if entries else None


def attested_time() -> bytes:
    return json.dumps({"iat": int(time.time())}).encode("utf-8")


def channel_identity(session_id: str, kernel_id: str) -> ChannelIdentity:
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(UTC)
    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"kernel.{kernel_id}"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "backend.ai confidential session"),
    ])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - CHANNEL_CLOCK_SKEW)
        .not_valid_after(now + CHANNEL_LIFETIME)
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(f"kernel.{kernel_id}"),
                x509.UniformResourceIdentifier(f"backendai://session/{session_id}/{kernel_id}"),
            ]),
            critical=False,
        )
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    der = certificate.public_bytes(serialization.Encoding.DER)
    token = secrets.token_urlsafe(32)
    return ChannelIdentity(
        bundle=_archive({
            "channel/key.pem": key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ),
            "channel/cert.pem": certificate.public_bytes(serialization.Encoding.PEM),
            "channel/token": token.encode("ascii"),
        }),
        fingerprint=hashlib.sha256(der).hexdigest(),
        token=token,
        expires_at=now + CHANNEL_LIFETIME,
    )
