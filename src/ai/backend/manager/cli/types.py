from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
    from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
    from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
    from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient


@attrs.define(auto_attribs=True, frozen=True, slots=True)
class RedisConnectionSet:
    live: ValkeyLiveClient
    stat: ValkeyStatClient
    image: ValkeyImageClient
    stream: ValkeyStreamClient
