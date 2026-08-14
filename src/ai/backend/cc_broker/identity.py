import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

from ai.backend.cc_broker.errors import EmptySecret, PolicyError
from ai.backend.cc_broker.kbs import Kbs
from ai.backend.cc_broker.policy import Entry

CURVE = "P-256"


def _openssl(args: Sequence[str]) -> bytes:
    done = subprocess.run(["openssl", *args], capture_output=True, timeout=30, check=False)
    if done.returncode != 0:
        raise PolicyError(done.stderr.decode("utf-8", "replace").strip())
    return done.stdout


def private_key(directory: str, name: str) -> tuple[Path, bytes]:
    root = Path(directory)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = root / f"{name}.key"
    if not path.exists():
        previous = os.umask(0o177)
        try:
            _openssl([
                "genpkey",
                "-algorithm",
                "EC",
                "-pkeyopt",
                f"ec_paramgen_curve:{CURVE}",
                "-out",
                str(path),
            ])
        finally:
            os.umask(previous)
    material = path.read_bytes()
    if not material:
        raise EmptySecret(f"identity key {name}")
    return path, material


def signing_request(key_path: Path, subject: str, sans: Sequence[str]) -> bytes:
    if not subject or not sans:
        raise PolicyError(f"identity {key_path} needs a subject and at least one name")
    args = ["req", "-new", "-key", str(key_path), "-subj", subject, "-outform", "PEM"]
    args += ["-addext", "subjectAltName=" + ",".join(sans)]
    request = _openssl(args)
    if not request:
        raise EmptySecret(f"signing request for {subject}")
    return request


def material(kbs: Kbs, directory: str, entry: Entry, cache: dict[str, bytes]) -> bytes:
    name = entry.value
    key_path, key_bytes = private_key(directory, name)
    if entry.part == "key":
        return key_bytes
    if name not in cache:
        request = signing_request(key_path, entry.subject, entry.sans)
        cache[name] = kbs.certificate(name, request)
    return cache[name]
