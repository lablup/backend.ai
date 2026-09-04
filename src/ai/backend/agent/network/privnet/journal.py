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

Three records, all written *before* the host is mutated (a record with no device is reconciled away
on the next boot; a device with no record can be named by nobody):

- ``sessions/<session_id>`` — the validated network config the privnet set the session up from. It
  is what lets a restarted privnet rebuild the session's meta and re-derive its device names.
- ``attachments/<container_id>`` — the session it belongs to, and the overlay IP the privnet
  validated for it. Enough to re-derive the attach plan, which is what detach needs to give back
  the host veth and the container's address.
- ``peers/<session_id>`` — every validated peer VTEP whose XFRM state this session may own. It lets
  recovery rebuild shared node-pair ownership before removing a dead session.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import secrets
import stat
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_PRIVNET_STATE_DIR = Path("/var/lib/backend.ai/net-privnet")

#: A journal record is a small JSON object; anything larger is not one of ours, and reading it
#: whole would let a file planted under a record's name cost this process its memory.
_MAX_RECORD_BYTES = 1 << 20

_SESSIONS = "sessions"
_ATTACHMENTS = "attachments"
_PEERS = "peers"


class JournalUnusable(Exception):
    """The journal could not be read or written as a whole.

    Distinct from an empty journal, which is a complete answer. This one means the answer is
    unknown, and recovery must treat it as a failure rather than as "there was nothing".
    """


class JournalIncomplete(JournalUnusable):
    """Some records were there and could not be read.

    The dangerous shape, and the reason this is an exception rather than a log line: dropping the
    damaged record and returning the rest looks exactly like a successful read of a smaller
    journal. Recovery then leaves that session's tunnel down, prunes the VNI claim that was
    holding its devices, clears its own failure flag, and reports a healthy node -- after which
    the manager may hand that VNI to somebody else while the first session's bridge is still up.
    """


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

    def _open_kind_dir(self, kind: str) -> int:
        """A descriptor on ``<root>/<kind>``, refusing to follow a symlink into it.

        Every read and write below is relative to this descriptor rather than to a path resolved
        again per operation. This process holds CAP_DAC_OVERRIDE and CAP_NET_ADMIN, so a name it
        resolves is a name it can write anywhere on the host: with the journal under a directory
        the agent can write -- which is what a same-uid deployment means -- a symlink planted at a
        predictable name turns a SETUP_SESSION into an arbitrary privileged write. Reproducible in
        one line before this.
        """
        self._make_private_dir(self._dir / kind)
        fd = os.open(self._dir / kind, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            if not stat.S_ISDIR(os.fstat(fd).st_mode):
                raise JournalUnusable(f"privnet journal {kind!r} is not a directory")
        except BaseException:
            os.close(fd)
            raise
        return fd

    def _write(self, kind: str, key: str, payload: dict[str, Any]) -> None:
        dir_fd = self._open_kind_dir(kind)
        try:
            # Written through a temporary file: a half-written record read on the next boot would
            # name a session whose subnet we cannot parse, and the reconcile pass would skip it
            # forever.
            #
            # Unpredictable and exclusive. The old name was `.<key>.tmp`, which anything that
            # could write this directory could pre-create as a symlink -- and O_CREAT without
            # O_EXCL follows one. O_EXCL and O_NOFOLLOW together refuse both the symlink and any
            # file already sitting there.
            tmp = f".{secrets.token_hex(8)}.tmp"
            # 0600 from the moment it exists. A session record holds the overlay's IPsec key, and
            # this is the one component that holds CAP_NET_ADMIN — leaving the key at the umask's
            # mercy put it in a world-readable file (measured: 0664 in a 0775 directory). Creating
            # the file and then chmod-ing it would still leave a window where it is readable, so
            # the mode goes on the open() and is reasserted on the fd.
            fd = os.open(
                tmp,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=dir_fd,
            )
            try:
                os.fchmod(fd, 0o600)
                with os.fdopen(fd, "w") as f:
                    f.write(json.dumps(payload))
            except BaseException:
                with contextlib.suppress(OSError):
                    os.close(fd)
                with contextlib.suppress(OSError):
                    os.unlink(tmp, dir_fd=dir_fd)
                raise
            os.rename(tmp, key, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
        finally:
            os.close(dir_fd)

    def _read_all(self, kind: str) -> dict[str, dict[str, Any]]:
        """Every record of this kind, or an exception. Never a subset presented as the whole.

        A record that is there and cannot be read is not a record that is absent. Dropping it and
        returning the rest is indistinguishable from a smaller journal, and recovery acts on the
        difference: it leaves that session's tunnel down, prunes the VNI binding holding its
        devices, and reports the node recovered.
        """
        directory = self._dir / kind
        if not directory.is_dir():
            return {}
        out: dict[str, dict[str, Any]] = {}
        damaged: list[str] = []
        dir_fd = self._open_kind_dir(kind)
        try:
            with os.scandir(dir_fd) as entries:
                names = sorted(entry.name for entry in entries)
            for name in names:
                if name.startswith("."):
                    continue  # a temporary file of ours, mid-write
                payload = self._read_record(name, dir_fd, damaged)
                if payload is None:
                    continue
                if isinstance(payload, dict):
                    out[name] = payload
                else:
                    damaged.append(f"{name}: not an object")
        finally:
            os.close(dir_fd)
        if damaged:
            raise JournalIncomplete(
                f"{len(damaged)} privnet journal {kind} record(s) could not be read"
                f" ({'; '.join(sorted(damaged)[:5])}); refusing to treat them as absent"
            )
        return out

    def _read_record(self, name: str, dir_fd: int, damaged: list[str]) -> Any:
        """One record's parsed JSON, or None for an entry that is not one of ours.

        Opened relative to the already-verified directory and never following a symlink: this
        process can read anything on the host, and a record is an input the agent's own request
        named.
        """
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=dir_fd)
        except OSError as e:
            damaged.append(f"{name}: {e}")
            return None
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                return None  # a directory or a device: not one of ours
            return json.loads(os.read(fd, _MAX_RECORD_BYTES).decode())
        except (OSError, ValueError) as e:
            damaged.append(f"{name}: {e}")
            return None
        finally:
            os.close(fd)

    async def record_session(self, session_id: str, network_config: dict[str, Any]) -> None:
        await asyncio.to_thread(self._write, _SESSIONS, session_id, network_config)

    async def forget_session(self, session_id: str) -> None:
        await asyncio.gather(
            asyncio.to_thread(self._path(_SESSIONS, session_id).unlink, True),
            asyncio.to_thread(self._path(_PEERS, session_id).unlink, True),
        )

    async def sessions(self) -> dict[str, dict[str, Any]]:
        """``{session_id: network_config}`` for every session this privnet set up and has not
        torn down."""
        return await asyncio.to_thread(self._read_all, _SESSIONS)

    async def record_peers(self, session_id: str, peer_vteps: Sequence[str]) -> None:
        """Record every peer whose host state this session may own.

        Callers write additions before programming the host and remove a peer only after its
        teardown lands. A crash can therefore over-record an entry, but cannot strand an
        unrecorded XFRM pair that recovery would never remove.
        """
        await asyncio.to_thread(
            self._write,
            _PEERS,
            session_id,
            {"vteps": sorted(set(peer_vteps))},
        )

    async def peers(self) -> dict[str, tuple[str, ...]]:
        """``{session_id: peer_vteps}`` for host state each session may own."""
        records: dict[str, tuple[str, ...]] = {}
        for session_id, payload in (await asyncio.to_thread(self._read_all, _PEERS)).items():
            raw_vteps = payload.get("vteps")
            if not isinstance(raw_vteps, list) or not all(
                isinstance(vtep, str) for vtep in raw_vteps
            ):
                # A record that exists and does not say what it must say. Its session may still be
                # holding XFRM state for peers this would silently forget.
                raise JournalIncomplete(
                    f"privnet peer record for session {session_id} does not list VTEPs"
                )
            records[session_id] = tuple(sorted(set(raw_vteps)))
        return records

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
                raise JournalIncomplete(
                    f"privnet attach record for container {container_id} names no session"
                )
            overlay_ip = payload.get("overlay_ip")
            records[container_id] = AttachRecord(
                session_id=session_id,
                overlay_ip=overlay_ip if isinstance(overlay_ip, str) else None,
            )
        return records
