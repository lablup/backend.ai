from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Final, Mapping, TypedDict

import attrs
import trafaret as t

from ai.backend.common import validators as tx
from ai.backend.watcher.base import BaseWatcher, BaseWatcherConfig
from ai.backend.watcher.defs import WatcherName
from ai.backend.watcher.plugin import AbstractWatcherPlugin

DEFAULT_FILE_IO_TIMEOUT: Final = 60


class EventConfig(TypedDict):
    connect_server: bool
    consumer_group: str


@attrs.define(slots=True)
class StorageWatcherConfig(BaseWatcherConfig):
    bai_uid: int
    bai_gid: int
    service_name: str
    poll_directory_mount: bool
    ignore_mount_event: bool
    event: EventConfig

    def to_json(self) -> dict[str, Any]:
        return {
            "bai_uid": self.bai_uid,
            "bai_gid": self.bai_gid,
            "service_name": self.service_name,
            "poll_directory_mount": self.poll_directory_mount,
            "ignore_mount_event": self.ignore_mount_event,
            "event": self.event,
        }

    @classmethod
    def as_trafaret(cls) -> t.Trafaret:
        return t.Dict({
            tx.AliasedKey(["bai_uid", "bai-uid"]): t.Int,
            tx.AliasedKey(["bai_gid", "bai-gid"]): t.Int,
            tx.AliasedKey(["service_name", "service-name"]): t.String(allow_blank=False),
            tx.AliasedKey(
                ["poll_directory_mount", "poll-directory-mount"], default=False
            ): t.ToBool,
            tx.AliasedKey(["ignore_mount_event", "ignore-mount-event"], default=False): t.ToBool,
            t.Key("event"): t.Dict({
                tx.AliasedKey(["connect_server", "connect-server"], default=False): t.ToBool,
                tx.AliasedKey(["consumer_group", "consumer-group"], default=None): t.Null
                | t.String,
            }),
        })


class StorageWatcher(BaseWatcher[StorageWatcherConfig]):
    name = WatcherName("storage-watcher")

    async def init(self) -> None:
        return

    async def shutdown(self) -> None:
        return

    async def chown(self, directory: str | Path, uid: int, gid: int) -> None:
        os.chown(directory, uid, gid)


class StorageWatcherPlugin(AbstractWatcherPlugin):
    async def init(self, context: Any = None) -> None:
        return

    async def cleanup(self) -> None:
        return

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = plugin_config

    def get_watcher_class(
        self,
    ) -> tuple[type[StorageWatcher], type[StorageWatcherConfig]]:
        return StorageWatcher, StorageWatcherConfig
