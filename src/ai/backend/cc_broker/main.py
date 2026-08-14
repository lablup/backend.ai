import argparse
import json
import logging
import os
import random
import socket
import sys
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ai.backend.cc_broker.clock import TrustedClock, claims, measurements, platform_status
from ai.backend.cc_broker.errors import (
    BrokerUnreachable,
    ClockUntrusted,
    EmptySecret,
    PolicyError,
    ReleaseDenied,
)
from ai.backend.cc_broker.identity import material
from ai.backend.cc_broker.kbs import Kbs
from ai.backend.cc_broker.policy import Entry, load
from ai.backend.cc_broker.render import render
from ai.backend.cc_broker.serve import CredentialServer, DecisionLog

logger = logging.getLogger(__name__)

CredentialStore = dict[tuple[str, str], bytes]
CredentialTable = dict[tuple[str, str], Entry]


def notify(state: str) -> None:
    address = os.environ.get("NOTIFY_SOCKET")
    if not address:
        return
    if address.startswith("@"):
        address = "\0" + address[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.connect(address)
        sock.sendall(state.encode("ascii"))


def collect(kbs: Kbs, broker: dict[str, Any], table: CredentialTable) -> CredentialStore:
    fetched: dict[str, bytes] = {}
    issued: dict[str, bytes] = {}

    def fetch(path: str) -> bytes:
        if path not in fetched:
            fetched[path] = kbs.resource(path)
        return fetched[path]

    store: CredentialStore = {}
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


def episode(
    kbs: Kbs,
    broker: dict[str, Any],
    table: CredentialTable,
    clock: TrustedClock,
    log: DecisionLog,
) -> CredentialStore:
    token = kbs.attest()
    body = claims(token)
    observed = time.time()
    attested = clock.take(body)
    logger.info(
        "wall clock read %.0f, attestation says %.0f, clock now %.0f",
        observed,
        attested,
        time.time(),
    )
    status = platform_status(body)
    quoted = measurements(body)
    log.record("platform", json.dumps(status, sort_keys=True), "credential-broker", "")
    with (Path(broker["identity_dir"]) / "platform-status.json").open("w") as f:
        json.dump({"appraisal": status, "measurements": quoted}, f, sort_keys=True)
    logger.info("appraisal %s", json.dumps(status, sort_keys=True))
    for field, value in sorted(quoted.items()):
        logger.info("%s=%s", field, value)
    return collect(kbs, broker, table)


def carry(path: str, log: DecisionLog) -> None:
    try:
        with Path(path).open(encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
    except (OSError, ValueError) as exc:
        logger.info("no unlock verdicts to carry forward (%s)", exc)
        return
    for entry in entries:
        log.record(entry["verdict"], entry["clause"], entry["unit"], entry["credential"])
    logger.info("carried %d unlock verdicts into the decision log", len(entries))


def renew(
    kbs: Kbs,
    broker: dict[str, Any],
    table: CredentialTable,
    clock: TrustedClock,
    log: DecisionLog,
    server: CredentialServer,
    period: float,
    jitter: float,
) -> None:
    while True:
        time.sleep(period + random.uniform(0, jitter))
        try:
            server.store = episode(kbs, broker, table, clock, log)
        except ClockUntrusted as exc:
            log.record("clock-untrusted", str(exc), "credential-broker", "")
        except (BrokerUnreachable, ReleaseDenied, EmptySecret, PolicyError) as exc:
            log.record("renewal-failed", type(exc).__name__ + ": " + str(exc), "", "")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="backendai-credential-broker")
    parser.add_argument("--policy", default="/etc/backendai/credential-policy.toml")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        format="credential-broker: %(message)s",
        level=logging.INFO,
    )

    broker, table = load(args.policy)
    Path(broker["identity_dir"]).mkdir(mode=0o700, parents=True, exist_ok=True)
    log = DecisionLog(
        broker.get("decision_log", "/var/lib/backendai/log/backendai-credentials.jsonl"),
        broker.get("durable_root", "/var/lib/backendai"),
    )
    carry(broker.get("unlock_verdicts", "/run/backendai-unlock.jsonl"), log)
    kbs = Kbs(
        broker["url"],
        broker["client"],
        broker.get("certificate_plugin", "external/pkix"),
        broker.get("timeout_seconds", 30),
        broker["identity_dir"],
    )
    clock = TrustedClock(broker.get("clock_skew_bound_seconds", 60))

    attempts = broker.get("boot_attempts", 5)
    store: CredentialStore | None = None
    for attempt in range(attempts):
        try:
            store = episode(kbs, broker, table, clock, log)
            break
        except BrokerUnreachable as exc:
            log.record("unreachable", str(exc), "", "")
            if attempt == attempts - 1:
                logger.error("key broker unreachable: %s", exc)
                return 1
            time.sleep(broker.get("boot_backoff_seconds", 5) * (attempt + 1))
        except (ReleaseDenied, EmptySecret, PolicyError) as exc:
            log.record("fatal", type(exc).__name__ + ": " + str(exc), "", "")
            logger.error("%s: %s", type(exc).__name__, exc)
            return 1

    if store is None:
        logger.error("broker.boot_attempts must be at least 1")
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
