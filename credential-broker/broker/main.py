import argparse
import json
import os
import random
import socket
import sys
import threading
import time

from .clock import TrustedClock, claims, measurements, platform_status
from .errors import BrokerUnreachable, EmptySecret, PolicyError, ReleaseDenied
from .identity import material
from .kbs import Kbs
from .policy import load
from .render import render
from .serve import CredentialServer, DecisionLog


def notify(state):
    address = os.environ.get("NOTIFY_SOCKET")
    if not address:
        return
    if address.startswith("@"):
        address = "\0" + address[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.connect(address)
        sock.sendall(state.encode("ascii"))


def collect(kbs, broker, table):
    fetched = {}
    issued = {}

    def fetch(path):
        if path not in fetched:
            fetched[path] = kbs.resource(path)
        return fetched[path]

    store = {}
    for key, entry in table.items():
        if entry.kind == "resource":
            value = fetch(entry.value)
        elif entry.kind == "render":
            value = render(broker["template_dir"], entry.value, fetch)
        else:
            value = material(kbs, broker["identity_dir"], entry, issued)
        if not value:
            raise EmptySecret(f"{entry.unit}/{entry.name}")
        store[key] = value
    return store


def episode(kbs, broker, table, clock, log):
    token = kbs.attest()
    body = claims(token)
    observed = time.time()
    attested = clock.take(body)
    print(
        f"credential-broker: wall clock read {observed:.0f}, attestation says "
        f"{attested:.0f}, clock now {time.time():.0f}",
        file=sys.stderr,
        flush=True,
    )
    status = platform_status(body)
    quoted = measurements(body)
    log.record("platform", json.dumps(status, sort_keys=True), "credential-broker", "")
    with open(os.path.join(broker["identity_dir"], "platform-status.json"), "w") as f:
        json.dump({"appraisal": status, "measurements": quoted}, f, sort_keys=True)
    print(
        "credential-broker: appraisal " + json.dumps(status, sort_keys=True),
        file=sys.stderr,
        flush=True,
    )
    for field, value in sorted(quoted.items()):
        print(f"credential-broker: {field}={value}", file=sys.stderr, flush=True)
    return collect(kbs, broker, table)


def renew(kbs, broker, table, clock, log, server, period, jitter):
    while True:
        time.sleep(period + random.uniform(0, jitter))
        try:
            server.store = episode(kbs, broker, table, clock, log)
        except (BrokerUnreachable, ReleaseDenied, EmptySecret, PolicyError) as exc:
            log.record("renewal-failed", type(exc).__name__ + ": " + str(exc), "", "")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="backendai-credential-broker")
    parser.add_argument("--policy", default="/etc/backendai/credential-policy.toml")
    args = parser.parse_args(argv)

    broker, table = load(args.policy)
    os.makedirs(broker["identity_dir"], mode=0o700, exist_ok=True)
    log = DecisionLog(broker.get("decision_log", "/var/log/backendai-credentials.jsonl"))
    kbs = Kbs(
        broker["url"],
        broker["client"],
        broker.get("certificate_plugin", "external/pkix"),
        broker.get("timeout_seconds", 30),
        broker["identity_dir"],
    )
    clock = TrustedClock(broker.get("clock_skew_bound_seconds", 60))

    attempts = broker.get("boot_attempts", 5)
    for attempt in range(attempts):
        try:
            store = episode(kbs, broker, table, clock, log)
            break
        except BrokerUnreachable as exc:
            log.record("unreachable", str(exc), "", "")
            if attempt == attempts - 1:
                print(f"key broker unreachable: {exc}", file=sys.stderr)
                return 1
            time.sleep(broker.get("boot_backoff_seconds", 5) * (attempt + 1))
        except (ReleaseDenied, EmptySecret, PolicyError) as exc:
            log.record("fatal", type(exc).__name__ + ": " + str(exc), "", "")
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    server = CredentialServer(broker["socket"], table, store, log)
    server.bind()
    notify("READY=1")
    threading.Thread(
        target=renew,
        args=(
            kbs,
            broker,
            table,
            clock,
            log,
            server,
            broker.get("renewal_seconds", 86400),
            broker.get("renewal_jitter_seconds", 3600),
        ),
        daemon=True,
    ).start()
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
