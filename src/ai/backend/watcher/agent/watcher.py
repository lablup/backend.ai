from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, TypedDict

import attrs
import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.watcher.base import BaseWatcher, BaseWatcherConfig
from ai.backend.watcher.defs import WatcherName
from ai.backend.watcher.plugin import AbstractWatcherPlugin


class EventConfig(TypedDict):
    connect_server: bool
    consumer_group: str


@attrs.define(slots=True)
class AgentWatcherConfig(BaseWatcherConfig):
    poll_directory_mount: bool
    ignore_mount_event: bool
    service_name: str
    soft_reset_available: bool
    ipc_base_path: Path
    event: EventConfig

    def to_json(self) -> dict[str, Any]:
        return {
            "poll_directory_mount": self.poll_directory_mount,
            "ignore_mount_event": self.ignore_mount_event,
            "service_name": self.service_name,
            "soft_reset_available": self.soft_reset_available,
            "ipc_base_path": self.ipc_base_path,
            "event": self.event,
        }

    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        return t.Dict({
            tx.AliasedKey(
                ["poll_directory_mount", "poll-directory-mount"], default=False
            ): t.ToBool,
            tx.AliasedKey(["ignore_mount_event", "ignore-mount-event"], default=False): t.ToBool,
            tx.AliasedKey(["service_name", "service-name"]): t.String(allow_blank=False),
            tx.AliasedKey(["soft_reset_available", "soft-reset-available"], default=True): t.Bool,
            tx.AliasedKey(["ipc_base_path", "ipc-base-path"]): tx.Path(type="dir"),
            t.Key("event"): t.Dict({
                tx.AliasedKey(["connect_server", "connect-server"], default=False): t.ToBool,
                tx.AliasedKey(["consumer_group", "consumer-group"], default=None): t.Null
                | t.String,
            }),
        })


class AgentWatcher(BaseWatcher[AgentWatcherConfig]):
    name = WatcherName("agent-watcher")

    async def init(self) -> None:
        return

    async def shutdown(self) -> None:
        return


class AgentWatcherPlugin(AbstractWatcherPlugin):
    async def init(self, context: Any = None) -> None:
        return

    async def cleanup(self) -> None:
        return

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = plugin_config

    def get_watcher_class(self) -> tuple[type[AgentWatcher], type[AgentWatcherConfig]]:
        return AgentWatcher, AgentWatcherConfig
