from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EXAScalerClientArgs:
    timeout: float


@dataclass(frozen=True)
class LustreServerConnection:
    name: str
    state: str
