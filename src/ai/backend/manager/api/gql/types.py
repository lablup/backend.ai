# ruff: noqa: E402
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from ai.backend.common.events.hub.hub import EventHub


@dataclass
class StrawberryGQLContext:
    processors: Processors
    config_provider: ManagerConfigProvider
    event_hub: EventHub
