from datetime import datetime

from cryptography import x509
from cryptography.x509.verification import PolicyBuilder, Store

from .types import RENEWAL_INTERVAL, PKIError


def load_pem_chain(pem: bytes) -> list[x509.Certificate]:
    chain = x509.load_pem_x509_certificates(pem)
    if not chain:
        raise PKIError("empty certificate chain")
    return chain


def verify_chain(
    leaf_pem: bytes,
    intermediates_pem: bytes,
    root_pem: bytes,
    dns_name: str,
    now: datetime,
) -> list[x509.Certificate]:
    verifier = (
        PolicyBuilder()
        .store(Store(load_pem_chain(root_pem)))
        .time(now)
        .build_server_verifier(x509.DNSName(dns_name))
    )
    return verifier.verify(
        x509.load_pem_x509_certificate(leaf_pem),
        load_pem_chain(intermediates_pem) if intermediates_pem else [],
    )


def needs_renewal(certificate_pem: bytes, now: datetime) -> bool:
    certificate = x509.load_pem_x509_certificate(certificate_pem)
    return certificate.not_valid_after_utc - now <= RENEWAL_INTERVAL
