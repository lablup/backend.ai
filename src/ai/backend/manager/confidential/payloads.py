from __future__ import annotations

import io
import json
import tarfile
import time
from collections.abc import Mapping
from typing import Any, Final

from ai.backend.common.types import ClusterSSHKeyPair

TIME_RESOURCE: Final = "default/backendai/time"


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
