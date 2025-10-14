# ruff: noqa: E402
from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.services.processors import Processors


@dataclass
class StrawberryGQLContext:
    processors: Processors
    config_provider: ManagerConfigProvider
