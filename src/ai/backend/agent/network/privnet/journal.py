"""What the privileged privnet must remember across its own restart (BEP-1062).

The agent recovers by reading durable ground truth: containerd's labels say which container belongs
to which session, and etcd holds each session's meta and each endpoint's overlay IP. The privnet can
use neither. It holds no etcd client by design — it is the process that owns CAP_NET_ADMIN, and the
fewer things it talks to, the smaller the blast radius — and the trust model forbids taking that
state back from the agent, which is the very process privilege separation exists to contain: an
agent that could re-declare a session's subnet on the privnet's behalf could point a session's data
plane anywhere.

So the privnet journals what it derived *itself*, at the moment it derived it, and on boot replays
that against containerd (which it does trust: it already re-resolves every container's PID there).
Without this, a privnet restart leaves the node's devices up but the daemon that owns them empty:
every later verb for a pre-restart session is refused ("before session setup"), and a teardown is
worse than refused — it silently succeeds while the bridge, the vxlan device and the session's
node-local subnet block are never released.

Two records, both written *before* the host is mutated (a record with no device is reconciled away
on the next boot; a device with no record can be named by nobody):

- ``sessions/<session_id>`` — the validated network config the privnet set the session up from. It
  is what lets a restarted privnet rebuild the session's meta and re-derive its device names.
- ``attachments/<container_id>`` — the session it belongs to, and the overlay IP the privnet
  validated for it. Enough to re-derive the attach plan, which is what detach needs to give back
  the host veth and the container's address.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_PRIVNET_STATE_DIR = Path("/var/lib/backend.ai/net-privnet")

_SESSIONS = "sessions"
_ATTACHMENTS = "attachments"


@dataclass(frozen=True)
class AttachRecord:
    """One container's attachment, as the privnet itself resolved it."""

    session_id: str
    overlay_ip: str | None


class PrivNetJournal:
    """The privnet's own durable record of the sessions and attachments it owns."""

    _dir: Path

    def __init__(self, state_dir: Path | None = None) -> None:
        self._dir = state_dir if state_dir is not None else DEFAULT_PRIVNET_STATE_DIR

    def _path(self, kind: str, key: str) -> Path:
        return self._dir / kind / key

    def _make_private_dir(self, path: Path) -> None:
        """Create ``path`` and make sure it, and the journal root above it, are owner-only.

        ``mkdir``'s mode argument is masked by the process umask and is ignored entirely for a
        directory that already exists, so the mode is set explicitly — including on a tree an
        earlier release left world-readable.
        """
        path.mkdir(parents=True, exist_ok=True)
        for d in (self._dir, path):
            with contextlib.suppress(OSError):
                d.chmod(0o700)

    def _write(self, kind: str, key: str, payload: dict[str, Any]) -> None:
        path = self._path(kind, key)
        self._make_private_dir(path.parent)
        # Write through a temporary file: a half-written record read on the next boot would name a
        # session whose subnet we cannot parse, and the reconcile pass would skip it forever.
        tmp = path.with_name(f".{path.name}.tmp")
        # 0600 from the moment it exists. A session record holds the overlay's IPsec key, and this
        # is the one component that holds CAP_NET_ADMIN — leaving the key at the umask's mercy put
        # it in a world-readable file (measured: 0664 in a 0775 directory). Creating the file and
        # then chmod-ing it would still leave a window where it is readable, so the mode goes on
        # the open() and is reasserted on the fd in case the temp file survived a crash.
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(json.dumps(payload))
        except BaseException:
            with contextlib.suppress(OSError):
                os.close(fd)
            raise
        tmp.replace(path)

    def _read_all(self, kind: str) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        directory = self._dir / kind
        if not directory.is_dir():
            return out
        for entry in sorted(directory.iterdir()):
            if not entry.is_file() or entry.name.startswith("."):
                continue
            try:
                payload = json.loads(entry.read_text())
            except (OSError, json.JSONDecodeError):
                log.warning("dropping unreadable privnet journal record {}", entry)
                continue
            if isinstance(payload, dict):
                out[entry.name] = payload
        return out

    async def record_session(self, session_id: str, network_config: dict[str, Any]) -> None:
        await asyncio.to_thread(self._write, _SESSIONS, session_id, network_config)

    async def forget_session(self, session_id: str) -> None:
        await asyncio.to_thread(self._path(_SESSIONS, session_id).unlink, True)

    async def sessions(self) -> dict[str, dict[str, Any]]:
        """``{session_id: network_config}`` for every session this privnet set up and has not
        torn down."""
        return await asyncio.to_thread(self._read_all, _SESSIONS)

    async def record_attachment(
        self, container_id: str, session_id: str, overlay_ip: str | None
    ) -> None:
        await asyncio.to_thread(
            self._write,
            _ATTACHMENTS,
            container_id,
            {"session_id": session_id, "overlay_ip": overlay_ip},
        )

    async def forget_attachment(self, container_id: str) -> None:
        await asyncio.to_thread(self._path(_ATTACHMENTS, container_id).unlink, True)

    async def attachments(self) -> dict[str, AttachRecord]:
        """``{container_id: AttachRecord}`` for every container this privnet attached and has not
        detached."""
        records: dict[str, AttachRecord] = {}
        for container_id, payload in (
            await asyncio.to_thread(self._read_all, _ATTACHMENTS)
        ).items():
            session_id = payload.get("session_id")
            if not isinstance(session_id, str):
                log.warning("dropping privnet attach record without a session: {}", container_id)
                continue
            overlay_ip = payload.get("overlay_ip")
            records[container_id] = AttachRecord(
                session_id=session_id,
                overlay_ip=overlay_ip if isinstance(overlay_ip, str) else None,
            )
        return records
