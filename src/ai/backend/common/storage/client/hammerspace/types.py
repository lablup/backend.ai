from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HammerspaceClientArgs:
    address: str
    username: str
    password: str
    verify_ssl: bool
    timeout: float


@dataclass(frozen=True)
class HammerspaceSite:
    name: str
    type: str
