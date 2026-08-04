from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .types import (
    CLOCK_SKEW_ALLOWANCE,
    LEAF_LIFETIME,
    IssuanceRefused,
    WorkloadIdentity,
)


def _subject_alternative_names(identity: WorkloadIdentity) -> x509.SubjectAlternativeName:
    entries: list[x509.GeneralName] = [x509.UniformResourceIdentifier(identity.uri)]
    entries.extend(x509.DNSName(name) for name in identity.dns_names)
    return x509.SubjectAlternativeName(entries)


def generate_key_and_request(identity: WorkloadIdentity) -> tuple[bytes, bytes]:
    key = ec.generate_private_key(ec.SECP256R1())
    request = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, identity.common_name)]))
        .add_extension(_subject_alternative_names(identity), critical=False)
        .sign(key, hashes.SHA256())
    )
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return key_pem, request.public_bytes(serialization.Encoding.PEM)


def issue_leaf(
    request_pem: bytes,
    identity: WorkloadIdentity,
    issuer_certificate_pem: bytes,
    issuer_key_pem: bytes,
    now: datetime,
    lifetime: timedelta = LEAF_LIFETIME,
) -> bytes:
    if lifetime > LEAF_LIFETIME:
        raise IssuanceRefused(f"requested lifetime {lifetime} exceeds {LEAF_LIFETIME}")
    request = x509.load_pem_x509_csr(request_pem)
    if not request.is_signature_valid:
        raise IssuanceRefused("certificate request signature does not verify")
    authorised = _subject_alternative_names(identity)
    try:
        requested = request.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    except x509.ExtensionNotFound:
        requested = authorised
    if set(requested) != set(authorised):
        raise IssuanceRefused(f"request names {set(requested)} do not match authorised {set(authorised)}")

    issuer = x509.load_pem_x509_certificate(issuer_certificate_pem)
    issuer_key = serialization.load_pem_private_key(issuer_key_pem, password=None)
    if not isinstance(issuer_key, ec.EllipticCurvePrivateKey):
        raise IssuanceRefused("issuer key is not an elliptic-curve signing key")
    certificate = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, identity.common_name)]))
        .issuer_name(issuer.subject)
        .public_key(request.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - CLOCK_SKEW_ALLOWANCE)
        .not_valid_after(now + lifetime)
        .add_extension(authorised, critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([
                x509.ExtendedKeyUsageOID.SERVER_AUTH,
                x509.ExtendedKeyUsageOID.CLIENT_AUTH,
            ]),
            critical=False,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(request.public_key()), critical=False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer.public_key()),
            critical=False,
        )
        .sign(issuer_key, hashes.SHA256())
    )
    return certificate.public_bytes(serialization.Encoding.PEM)
