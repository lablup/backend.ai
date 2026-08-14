import json
import os
import socket
import time
from pathlib import Path

from ai.backend.cc_broker.errors import DecisionLogNotDurable, SocketNotBound
from ai.backend.cc_broker.policy import Entry, peer_credential


class DecisionLog:
    path: Path

    def __init__(self, path: str, durable_root: str) -> None:
        if not path.startswith(durable_root):
            raise DecisionLogNotDurable(f"{path} is not under {durable_root}")
        if not Path(durable_root).is_mount():
            raise DecisionLogNotDurable(f"{durable_root} is not a mount point")
        self.path = Path(path)
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    def record(self, verdict: str, clause: str, unit: str, name: str) -> None:
        line = json.dumps(
            {
                "at": time.time(),
                "verdict": verdict,
                "clause": clause,
                "unit": unit,
                "credential": name,
            },
            sort_keys=True,
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())


class CredentialServer:
    path: Path
    table: dict[tuple[str, str], Entry]
    store: dict[tuple[str, str], bytes]
    log: DecisionLog
    sock: socket.socket | None

    def __init__(
        self,
        path: str,
        table: dict[tuple[str, str], Entry],
        store: dict[tuple[str, str], bytes],
        log: DecisionLog,
    ) -> None:
        self.path = Path(path)
        self.table = table
        self.store = store
        self.log = log
        self.sock = None

    def bind(self) -> None:
        staging = self.path.with_name(self.path.name + ".staged")
        for stale in (staging, self.path):
            stale.unlink(missing_ok=True)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(str(staging))
        staging.chmod(0o600)
        sock.listen(64)
        staging.rename(self.path)
        self.sock = sock

    def serve_forever(self) -> None:
        if self.sock is None:
            raise SocketNotBound(f"{self.path} has not been bound")
        while True:
            conn, _ = self.sock.accept()
            with conn:
                self.handle(conn)

    def handle(self, conn: socket.socket) -> None:
        try:
            peer = conn.getpeername()
        except OSError:
            peer = b""
        pair = peer_credential(peer)
        if pair is None:
            self.log.record("deny", "unparseable-peer-name", repr(peer), "")
            return
        unit, name = pair
        if pair not in self.table:
            self.log.record("deny", "not-in-policy-table", unit, name)
            return
        data = self.store.get(pair)
        if not data:
            self.log.record("deny", "zero-length-material", unit, name)
            return
        try:
            conn.sendall(data)
        except OSError:
            self.log.record("deny", "peer-hung-up", unit, name)
            return
        self.log.record("allow", "", unit, name)
