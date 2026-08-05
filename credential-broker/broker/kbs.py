import base64
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

from .errors import BrokerUnreachable, EmptySecret, ReleaseDenied

DENIAL_MARKERS = (
    "denied",
    "deny",
    "not allowed",
    "policy",
    "403",
    "401",
    "attestation failed",
)


def _decode(blob):
    text = blob.strip()
    if not text:
        return b""
    try:
        return base64.b64decode(text, validate=True)
    except (ValueError, base64.binascii.Error):
        return blob


class Kbs:
    def __init__(self, url, client, plugin, timeout, workdir):
        self.url = url.rstrip("/")
        self.client = client
        self.plugin = plugin
        self.timeout = timeout
        self.key_path = os.path.join(workdir, "tee-key.pem")
        self.token_path = os.path.join(workdir, "attestation-token")
        self.reuse = True
        self.token = b""

    def _run(self, args, payload=None):
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

    def _transport_key(self):
        if not os.path.exists(self.key_path):
            previous = os.umask(0o177)
            try:
                done = subprocess.run(
                    ["openssl", "genrsa", "-traditional", "-out", self.key_path, "2048"],
                    capture_output=True,
                    timeout=self.timeout,
                    check=False,
                )
            finally:
                os.umask(previous)
            if done.returncode != 0:
                raise BrokerUnreachable(done.stderr.decode("utf-8", "replace").strip())
        return self.key_path

    def _held(self, base, extra):
        if not self.reuse:
            return self._run(base)
        try:
            return self._run(base + extra())
        except (BrokerUnreachable, ReleaseDenied) as exc:
            print(
                f"credential-broker: the broker would not carry a held attestation "
                f"session ({exc}); falling back to one handshake per resource",
                file=sys.stderr,
                flush=True,
            )
            self.reuse = False
            return self._run(base)

    def attest(self):
        token = self._held(
            ["attest"], lambda: ["--tee-key-file", self._transport_key()]
        ).strip()
        if not token:
            raise BrokerUnreachable("attestation produced no token")
        if self.reuse:
            previous = os.umask(0o177)
            try:
                with open(self.token_path, "wb") as f:
                    f.write(token)
            finally:
                os.umask(previous)
        self.token = token
        return token

    def resource(self, path):
        base = ["get-resource", "--path", path]
        if self.token:
            material = _decode(self._held(
                base,
                lambda: ["--tee-key-file", self.key_path,
                         "--attestation-token", self.token_path],
            ))
        else:
            material = _decode(self._run(base))
        if not material:
            raise EmptySecret(path)
        return material

    def certificate(self, name, request):
        if not self.token:
            raise BrokerUnreachable("no attestation token held for certificate issuance")
        query = urllib.parse.urlencode(
            [
                ("identity", name),
                ("csr", base64.urlsafe_b64encode(request).decode("ascii")),
            ]
        )
        get = urllib.request.Request(
            f"{self.url}/kbs/v0/{self.plugin}/issue?{query}",
            headers={"Authorization": b"Bearer " + self.token},
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
