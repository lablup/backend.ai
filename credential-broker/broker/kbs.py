import base64
import subprocess
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
    def __init__(self, url, client, plugin, timeout):
        self.url = url.rstrip("/")
        self.client = client
        self.plugin = plugin
        self.timeout = timeout
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

    def attest(self):
        token = self._run(["attest"]).strip()
        if not token:
            raise BrokerUnreachable("attestation produced no token")
        self.token = token
        return token

    def resource(self, path):
        material = _decode(self._run(["get-resource", "--path", path]))
        if not material:
            raise EmptySecret(path)
        return material

    def certificate(self, name, subject, sans, request):
        if not self.token:
            raise BrokerUnreachable("no attestation token held for certificate issuance")
        query = urllib.parse.urlencode(
            [
                ("identity", name),
                ("subject", subject),
                *(("san", entry) for entry in sans),
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
                raise ReleaseDenied(f"certificate issuance for {subject}: {exc}") from exc
            raise BrokerUnreachable(str(exc)) from exc
        except (urllib.error.URLError, OSError) as exc:
            raise BrokerUnreachable(str(exc)) from exc
        if not chain or b"BEGIN CERTIFICATE" not in chain:
            raise EmptySecret(f"certificate chain for {subject}")
        return chain
