import argparse
import base64
import concurrent.futures
import datetime
import ipaddress
import json
import sys

import grpc
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509.oid import NameOID

import plugin_pb2
import plugin_pb2_grpc

ATTRIBUTES = {
    "CN": NameOID.COMMON_NAME,
    "O": NameOID.ORGANIZATION_NAME,
    "OU": NameOID.ORGANIZATIONAL_UNIT_NAME,
    "C": NameOID.COUNTRY_NAME,
    "ST": NameOID.STATE_OR_PROVINCE_NAME,
    "L": NameOID.LOCALITY_NAME,
}


class Refused(Exception):
    pass


def distinguished_name(subject):
    parts = [piece for piece in subject.split("/") if piece]
    if not parts:
        raise Refused(f"profile subject {subject!r} names nothing")
    attributes = []
    for piece in parts:
        key, _, value = piece.partition("=")
        oid = ATTRIBUTES.get(key.upper())
        if oid is None or not value:
            raise Refused(f"profile subject component {piece!r} is not usable")
        attributes.append(x509.NameAttribute(oid, value))
    return x509.Name(attributes)


def alternative_name(entry):
    kind, _, value = entry.partition(":")
    kind = kind.upper()
    if not value:
        raise Refused(f"profile name {entry!r} carries no value")
    if kind == "DNS":
        return x509.DNSName(value)
    if kind == "URI":
        return x509.UniformResourceIdentifier(value)
    if kind == "EMAIL":
        return x509.RFC822Name(value)
    if kind == "IP":
        return x509.IPAddress(ipaddress.ip_address(value))
    raise Refused(f"profile name {entry!r} uses an unsupported kind")


def load_profiles(path):
    with open(path, "rb") as f:
        document = json.load(f)
    profiles = {}
    for name, raw in document.items():
        subject = distinguished_name(raw["subject"])
        names = [alternative_name(entry) for entry in raw["sans"]]
        if not names:
            raise Refused(f"profile {name} declares no subject alternative name")
        profiles[name] = (subject, names, int(raw.get("validity_days", 30)))
    if not profiles:
        raise Refused("the profile table is empty")
    return profiles


class Authority:
    def __init__(self, certificate_path, key_path, profiles):
        with open(certificate_path, "rb") as f:
            self.certificate_pem = f.read()
        self.certificate = x509.load_pem_x509_certificate(self.certificate_pem)
        with open(key_path, "rb") as f:
            self.key = serialization.load_pem_private_key(f.read(), password=None)
        self.profiles = profiles

    def issue(self, identity, request):
        profile = self.profiles.get(identity)
        if profile is None:
            raise Refused(f"identity {identity!r} has no profile")
        subject, names, validity_days = profile
        if not request.is_signature_valid:
            raise Refused(f"the signing request for {identity!r} is not self-signed")
        now = datetime.datetime.now(datetime.timezone.utc)
        public_key = request.public_key()
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.certificate.subject)
            .public_key(public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=5))
            .not_valid_after(now + datetime.timedelta(days=validity_days))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=True,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                True,
            )
            .add_extension(
                x509.ExtendedKeyUsage(
                    [
                        x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                        x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                    ]
                ),
                False,
            )
            .add_extension(x509.SubjectAlternativeName(names), False)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(public_key), False)
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(
                    self.certificate.public_key()
                ),
                False,
            )
        )
        leaf = builder.sign(self.key, hashes.SHA256())
        return leaf.public_bytes(serialization.Encoding.PEM) + self.certificate_pem


class Plugin(plugin_pb2_grpc.KbsPluginServicer):
    def __init__(self, authority):
        self.authority = authority

    def Handle(self, request, context):
        try:
            body = self.dispatch(request)
        except Refused as exc:
            print(f"pkix: refused: {exc}", file=sys.stderr, flush=True)
            return plugin_pb2.PluginResponse(
                body=str(exc).encode("utf-8"), status_code=403
            )
        return plugin_pb2.PluginResponse(body=body, status_code=200)

    def dispatch(self, request):
        if list(request.path) != ["issue"]:
            raise Refused(f"no route for {'/'.join(request.path)!r}")
        if request.method.upper() not in ("GET", "POST"):
            raise Refused(f"method {request.method} is not accepted")
        identity = request.query.get("identity", "")
        encoded = request.query.get("csr", "")
        if not identity or not encoded:
            raise Refused("an issuance needs both an identity and a signing request")
        try:
            pem = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
            signing_request = x509.load_pem_x509_csr(pem)
        except ValueError as exc:
            raise Refused(f"the signing request did not parse: {exc}") from exc
        chain = self.authority.issue(identity, signing_request)
        print(f"pkix: issued a chain for {identity}", file=sys.stderr, flush=True)
        return chain

    def ValidateAuth(self, request, context):
        return plugin_pb2.ValidateAuthResponse(requires_admin_auth=False)

    def NeedsEncryption(self, request, context):
        return plugin_pb2.NeedsEncryptionResponse(requires_payload_encryption=False)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="backendai-pkix-plugin")
    parser.add_argument("--ca-certificate", required=True)
    parser.add_argument("--ca-key", required=True)
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--listen", default="127.0.0.1:50051")
    parser.add_argument("--tls-certificate")
    parser.add_argument("--tls-key")
    args = parser.parse_args(argv)

    authority = Authority(args.ca_certificate, args.ca_key, load_profiles(args.profiles))
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=8))
    plugin_pb2_grpc.add_KbsPluginServicer_to_server(Plugin(authority), server)
    if args.tls_certificate and args.tls_key:
        with open(args.tls_certificate, "rb") as f:
            chain = f.read()
        with open(args.tls_key, "rb") as f:
            key = f.read()
        server.add_secure_port(
            args.listen, grpc.ssl_server_credentials([(key, chain)])
        )
    else:
        server.add_insecure_port(args.listen)
    server.start()
    print(f"pkix: serving on {args.listen}", file=sys.stderr, flush=True)
    server.wait_for_termination()
    return 0


if __name__ == "__main__":
    sys.exit(main())
