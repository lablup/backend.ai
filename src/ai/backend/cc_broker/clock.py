import base64
import json
import subprocess
import time
from collections.abc import Mapping
from typing import Any

from ai.backend.cc_broker.errors import ClockUntrusted


def claims(token: bytes | str) -> dict[str, Any]:
    text = token.decode("ascii", "replace") if isinstance(token, bytes) else token
    parts = text.strip().split(".")
    if len(parts) != 3:
        raise ClockUntrusted("attestation token is not a three-part JWT")
    payload = parts[1].encode("ascii")
    body = base64.urlsafe_b64decode(payload + b"=" * (-len(payload) % 4))
    return json.loads(body)


def issued_at(token_claims: Mapping[str, Any]) -> float:
    for field in ("iat", "nbf"):
        value = token_claims.get(field)
        if isinstance(value, (int, float)):
            return float(value)
    raise ClockUntrusted("attestation token carries no issued-at claim")


MEASUREMENTS = (
    "mr_td",
    "mr_config_id",
    "mr_seam",
    "rtmr_0",
    "rtmr_1",
    "rtmr_2",
    "rtmr_3",
    "xfam",
)


def measurements(token_claims: Mapping[str, Any]) -> dict[str, Any]:
    reported: dict[str, Any] = {}
    for submod in (token_claims.get("submods") or {}).values():
        if not isinstance(submod, dict):
            continue
        evidence = submod.get("ear.veraison.annotated-evidence") or {}
        body = ((evidence.get("tdx") or {}).get("quote") or {}).get("body") or {}
        for field in MEASUREMENTS:
            if body.get(field):
                reported[field] = body[field]
    return reported


def platform_status(token_claims: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    reported: dict[str, dict[str, Any]] = {}
    for name, submod in (token_claims.get("submods") or {}).items():
        if not isinstance(submod, dict):
            continue
        evidence = submod.get("ear.veraison.annotated-evidence") or {}
        hardware = evidence.get("tdx") or evidence.get("nvidia") or {}
        reported[name] = {
            "ear-status": submod.get("ear.status", "unstated"),
            "tcb-status": hardware.get("tcb_status", "unstated"),
            "collateral-expiration-status": hardware.get(
                "collateral_expiration_status", "unstated"
            ),
        }
    return reported or {"cpu0": {"ear-status": "unstated"}}


class TrustedClock:
    bound: float
    offset: float | None

    def __init__(self, bound_seconds: float) -> None:
        self.bound = bound_seconds
        self.offset = None

    def take(self, token_claims: Mapping[str, Any]) -> float:
        attested = issued_at(token_claims)
        counter = time.monotonic()
        if self.offset is None:
            if abs(time.time() - attested) > self.bound:
                subprocess.run(
                    ["date", "-u", "-s", f"@{int(attested)}"],
                    check=True,
                    timeout=10,
                )
            self.offset = attested - counter
            return attested
        drift = attested - (counter + self.offset)
        if abs(drift) > self.bound:
            raise ClockUntrusted(f"attested time drifted {drift:.1f}s from the hardware counter")
        self.offset = attested - counter
        return attested
