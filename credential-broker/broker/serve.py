import json
import os
import socket
import time

from .policy import peer_credential


class DecisionLog:
    def __init__(self, path):
        self.path = path

    def record(self, verdict, clause, unit, name):
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
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())


class CredentialServer:
    def __init__(self, path, table, store, log):
        self.path = path
        self.table = table
        self.store = store
        self.log = log
        self.sock = None

    def bind(self):
        staging = self.path + ".staged"
        for stale in (staging, self.path):
            try:
                os.unlink(stale)
            except FileNotFoundError:
                pass
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(staging)
        os.chmod(staging, 0o600)
        sock.listen(64)
        os.rename(staging, self.path)
        self.sock = sock

    def serve_forever(self):
        while True:
            conn, _ = self.sock.accept()
            with conn:
                self.handle(conn)

    def handle(self, conn):
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
