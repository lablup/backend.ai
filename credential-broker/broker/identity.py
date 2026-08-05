import os
import subprocess

from .errors import EmptySecret, PolicyError

CURVE = "P-256"


def _openssl(args):
    done = subprocess.run(
        ["openssl", *args], capture_output=True, timeout=30, check=False
    )
    if done.returncode != 0:
        raise PolicyError(done.stderr.decode("utf-8", "replace").strip())
    return done.stdout


def private_key(directory, name):
    os.makedirs(directory, mode=0o700, exist_ok=True)
    path = os.path.join(directory, name + ".key")
    if not os.path.exists(path):
        previous = os.umask(0o177)
        try:
            _openssl(
                [
                    "genpkey",
                    "-algorithm",
                    "EC",
                    "-pkeyopt",
                    f"ec_paramgen_curve:{CURVE}",
                    "-out",
                    path,
                ]
            )
        finally:
            os.umask(previous)
    with open(path, "rb") as f:
        material = f.read()
    if not material:
        raise EmptySecret(f"identity key {name}")
    return path, material


def signing_request(key_path, subject, sans):
    if not subject or not sans:
        raise PolicyError(f"identity {key_path} needs a subject and at least one name")
    args = ["req", "-new", "-key", key_path, "-subj", subject, "-outform", "PEM"]
    args += ["-addext", "subjectAltName=" + ",".join(sans)]
    request = _openssl(args)
    if not request:
        raise EmptySecret(f"signing request for {subject}")
    return request


def material(kbs, directory, entry, cache):
    name = entry.value
    key_path, key_bytes = private_key(directory, name)
    if entry.part == "key":
        return key_bytes
    if name not in cache:
        request = signing_request(key_path, entry.subject, entry.sans)
        cache[name] = kbs.certificate(name, request)
    return cache[name]
