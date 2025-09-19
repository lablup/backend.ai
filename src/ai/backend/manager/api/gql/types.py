# ruff: noqa: E402
from __future__ import annotations

import attrs

from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.services.processors import Processors


@attrs.define(auto_attribs=True, slots=True)
class StrawberryGQLContext:
    processors: Processors
    config_provider: ManagerConfigProvider
    event_hub: EventHub
    event_fetcher: EventFetcher
    valkey_bgtask: ValkeyBgtaskClient
