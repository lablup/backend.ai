import base64
import binascii
import logging
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path

from ai.backend.cc_broker.errors import BrokerUnreachable, EmptySecret, ReleaseDenied

logger = logging.getLogger(__name__)

DENIAL_MARKERS = (
    "denied",
    "deny",
    "not allowed",
    "policy",
    "403",
    "401",
    "attestation failed",
)


def _decode(blob: bytes) -> bytes:
    text = blob.strip()
    if not text:
        return b""
    try:
        return base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error):
        return blob


class Kbs:
    url: str
    client: str
    plugin: str
    timeout: float
    key_path: Path
    token_path: Path
    reuse: bool
    token: bytes

    def __init__(self, url: str, client: str, plugin: str, timeout: float, workdir: str) -> None:
        self.url = url.rstrip("/")
        self.client = client
        self.plugin = plugin
        self.timeout = timeout
        self.key_path = Path(workdir) / "tee-key.pem"
        self.token_path = Path(workdir) / "attestation-token"
        self.reuse = True
        self.token = b""

    def _run(self, args: Sequence[str], payload: bytes | None = None) -> bytes:
        try:
            done = subprocess.run(
                [self.client, "--url", self.url, *args],
                input=payload,
                capture_output=True,
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BrokerUnreachable(str(exc)) from exc
        if done.returncode == 0:
            return done.stdout
        detail = done.stderr.decode("utf-8", "replace").strip()
        lowered = detail.lower()
        if any(marker in lowered for marker in DENIAL_MARKERS):
            raise ReleaseDenied(detail)
        raise BrokerUnreachable(detail)

    def _transport_key(self) -> str:
        if not self.key_path.exists():
            previous = os.umask(0o177)
            try:
                done = subprocess.run(
                    ["openssl", "genrsa", "-traditional", "-out", str(self.key_path), "2048"],
                    capture_output=True,
                    timeout=self.timeout,
                    check=False,
                )
            finally:
                os.umask(previous)
            if done.returncode != 0:
                raise BrokerUnreachable(done.stderr.decode("utf-8", "replace").strip())
        return str(self.key_path)

    def _held(self, base: list[str], extra: Callable[[], list[str]]) -> bytes:
        if not self.reuse:
            return self._run(base)
        try:
            return self._run(base + extra())
        except (BrokerUnreachable, ReleaseDenied) as exc:
            logger.warning(
                "the broker would not carry a held attestation session (%s); "
                "falling back to one handshake per resource",
                exc,
            )
            self.reuse = False
            return self._run(base)

    def attest(self) -> bytes:
        token = self._held(["attest"], lambda: ["--tee-key-file", self._transport_key()]).strip()
        if not token:
            raise BrokerUnreachable("attestation produced no token")
        if self.reuse:
            previous = os.umask(0o177)
            try:
                self.token_path.write_bytes(token)
            finally:
                os.umask(previous)
        self.token = token
        return token

    def resource(self, path: str) -> bytes:
        base = ["get-resource", "--path", path]
        if self.token:
            material = _decode(
                self._held(
                    base,
                    lambda: [
                        "--tee-key-file",
                        str(self.key_path),
                        "--attestation-token",
                        str(self.token_path),
                    ],
                )
            )
        else:
            material = _decode(self._run(base))
        if not material:
            raise EmptySecret(path)
        return material

    def certificate(self, name: str, request: bytes) -> bytes:
        if not self.token:
            raise BrokerUnreachable("no attestation token held for certificate issuance")
        query = urllib.parse.urlencode([
            ("identity", name),
            ("csr", base64.urlsafe_b64encode(request).decode("ascii")),
        ])
        get = urllib.request.Request(
            f"{self.url}/kbs/v0/{self.plugin}/issue?{query}",
            headers={"Authorization": "Bearer " + self.token.decode("ascii")},
        )
        try:
            with urllib.request.urlopen(get, timeout=self.timeout) as response:
                chain = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise ReleaseDenied(f"certificate issuance for {name}: {exc}") from exc
            raise BrokerUnreachable(str(exc)) from exc
        except (urllib.error.URLError, OSError) as exc:
            raise BrokerUnreachable(str(exc)) from exc
        if not chain or b"BEGIN CERTIFICATE" not in chain:
            raise EmptySecret(f"certificate chain for {name}")
        return chain
