"""Tests for EventDispatcherPluginContext plugin isolation."""

from __future__ import annotations

from typing import Any, override
from unittest.mock import MagicMock

from ai.backend.common.events.types import AbstractEvent
from ai.backend.common.plugin.event import (
    AbstractEventDispatcherPlugin,
    EventDispatcherPluginContext,
)
from ai.backend.common.types import AgentId


class _RecordingPlugin(AbstractEventDispatcherPlugin):
    received: list[AbstractEvent]

    def __init__(self) -> None:
        super().__init__(plugin_config={}, local_config={})
        self.received = []

    @override
    async def update_plugin_config(self, plugin_config: Any) -> None:
        pass

    @override
    async def handle_event(self, source: AgentId, event: AbstractEvent) -> None:
        self.received.append(event)


class _RaisingPlugin(AbstractEventDispatcherPlugin):
    @override
    async def update_plugin_config(self, plugin_config: Any) -> None:
        pass

    @override
    async def handle_event(self, source: AgentId, event: AbstractEvent) -> None:
        raise RuntimeError("broken plugin")


def _make_context(
    plugins: dict[str, AbstractEventDispatcherPlugin],
) -> EventDispatcherPluginContext:
    ctx = EventDispatcherPluginContext(etcd=MagicMock(), local_config={})
    ctx.plugins = plugins
    return ctx


def _make_event() -> AbstractEvent:
    event = MagicMock(spec=AbstractEvent)
    event.event_name.return_value = "test_event"
    return event


class TestEventDispatcherPluginContextIsolation:
    """A misbehaving plugin must not disturb the caller or sibling plugins."""

    async def test_plugin_exception_does_not_propagate(self) -> None:
        ctx = _make_context({"broken": _RaisingPlugin(plugin_config={}, local_config={})})
        # Must not raise into the surrounding event handler.
        await ctx.handle_event(None, AgentId("i-test"), _make_event())

    async def test_sibling_plugins_still_receive_the_event(self) -> None:
        recording = _RecordingPlugin()
        ctx = _make_context({
            "broken": _RaisingPlugin(plugin_config={}, local_config={}),
            "healthy": recording,
        })
        event = _make_event()
        await ctx.handle_event(None, AgentId("i-test"), event)
        assert recording.received == [event]
