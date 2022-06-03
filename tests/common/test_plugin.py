import asyncio
import functools
from typing import (
    Any,
    Mapping,
)
from unittest.mock import AsyncMock

from ai.backend.common.plugin import (
    AbstractPlugin,
    BasePluginContext,
)
from ai.backend.common.plugin.hook import (
    HookPlugin,
    HookPluginContext,
    Reject,
    PASSED,
    REJECTED,
    ERROR,
    ALL_COMPLETED,
    FIRST_COMPLETED,
)

import pytest


class DummyPlugin(AbstractPlugin):

    def __init__(self, plugin_config, local_config) -> None:
        super().__init__(plugin_config, local_config)

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        pass


class DummyEntrypoint:

    def __init__(self, name: str, load_result: Any) -> None:
        self.name = name
        self._load_result = load_result

    def load(self) -> Any:
        return self._load_result


def mock_entrypoints_with_instance(plugin_group_name: str, *, mocked_plugin):
    # Since mocked_plugin is already an instance constructed via AsyncMock,
    # we emulate the original constructor using a lambda fucntion.
    yield DummyEntrypoint('dummy', lambda plugin_config, local_config: mocked_plugin)


def mock_entrypoints_with_class(plugin_group_name: str, *, plugin_cls):
    if isinstance(plugin_cls, list):
        yield from (DummyEntrypoint(getattr(p, '_entrypoint_name', 'dummy'), p) for p in plugin_cls)
    else:
        yield DummyEntrypoint('dummy', plugin_cls)


@pytest.mark.asyncio
async def test_plugin_context_init_cleanup(etcd, mocker):
    print('test plugin context init cleanup')
    mocked_plugin = AsyncMock(DummyPlugin)
    mocked_entrypoints = functools.partial(mock_entrypoints_with_instance,
                                           mocked_plugin=mocked_plugin)
    mocker.patch('ai.backend.common.plugin.pkg_resources.iter_entry_points', mocked_entrypoints)
    ctx = BasePluginContext(etcd, {})
    try:
        assert not ctx.plugins
        await ctx.init()
        assert ctx.plugins
        ctx.plugins['dummy'].init.assert_awaited_once()
    finally:
        await ctx.cleanup()
        ctx.plugins['dummy'].cleanup.assert_awaited_once()


@pytest.mark.asyncio
async def test_plugin_context_config(etcd, mocker):
    mocked_entrypoints = functools.partial(mock_entrypoints_with_class, plugin_cls=DummyPlugin)
    mocker.patch('ai.backend.common.plugin.pkg_resources.iter_entry_points', mocked_entrypoints)
    await etcd.put('config/plugins/XXX/dummy/etcd-key', 'etcd-value')
    ctx = BasePluginContext(
        etcd,
        {'local-key': 'local-value'},
    )
    try:
        assert not ctx.plugins
        await ctx.init()
        assert ctx.plugins
        assert isinstance(ctx.plugins['dummy'], DummyPlugin)
        ctx.plugins['dummy'].local_config['local-key'] == 'local-value'
        ctx.plugins['dummy'].plugin_config['etcd-key'] == 'etcd-value'
    finally:
        await ctx.cleanup()


@pytest.mark.asyncio
async def test_plugin_context_config_autoupdate(etcd, mocker):
    mocked_plugin = AsyncMock(DummyPlugin)
    mocked_entrypoints = functools.partial(mock_entrypoints_with_instance,
                                           mocked_plugin=mocked_plugin)
    mocker.patch('ai.backend.common.plugin.pkg_resources.iter_entry_points', mocked_entrypoints)
    await etcd.put_prefix('config/plugins/XXX/dummy', {'a': '1', 'b': '2'})
    ctx = BasePluginContext(
        etcd,
        {'local-key': 'local-value'},
    )
    try:
        await ctx.init()
        await asyncio.sleep(0.01)
        await etcd.put_prefix('config/plugins/XXX/dummy', {'a': '3', 'b': '4'})
        await asyncio.sleep(0.6)  # we should see the update only once
        await etcd.put_prefix('config/plugins/XXX/dummy', {'a': '5', 'b': '6'})
        await asyncio.sleep(0.3)
        print(mocked_plugin.update_plugin_config)
        args_list = mocked_plugin.update_plugin_config.await_args_list
        assert len(args_list) == 2
        assert args_list[0].args[0] == {'a': '3', 'b': '4'}
        assert args_list[1].args[0] == {'a': '5', 'b': '6'}
    finally:
        await ctx.cleanup()


class DummyHookPassingPlugin(HookPlugin):

    config_watch_enabled = False

    _entrypoint_name = 'hook-p'

    def get_handlers(self):
        return [
            ('HOOK1', self.hook1_handler),
            ('HOOK2', self.hook2_handler),
        ]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_config: Mapping[str, Any]) -> None:
        pass

    async def hook1_handler(self, arg1, arg2):
        assert arg1 == 'a'
        assert arg2 == 'b'
        return 1

    async def hook2_handler(self, arg1, arg2):
        assert arg1 == 'c'
        assert arg2 == 'd'
        return 2


class DummyHookRejectingPlugin(HookPlugin):

    config_watch_enabled = False

    _entrypoint_name = 'hook-r'

    def get_handlers(self):
        return [
            ('HOOK1', self.hook1_handler),
            ('HOOK2', self.hook2_handler),
        ]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_config: Mapping[str, Any]) -> None:
        pass

    async def hook1_handler(self, arg1, arg2):
        assert arg1 == 'a'
        assert arg2 == 'b'
        raise Reject('dummy rejected 1')

    async def hook2_handler(self, arg1, arg2):
        assert arg1 == 'c'
        assert arg2 == 'd'
        return 3


class DummyHookErrorPlugin(HookPlugin):

    config_watch_enabled = False

    _entrypoint_name = 'hook-e'

    def get_handlers(self):
        return [
            ('HOOK3', self.hook3_handler),
        ]

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, new_config: Mapping[str, Any]) -> None:
        pass

    async def hook3_handler(self, arg1, arg2):
        assert arg1 == 'e'
        assert arg2 == 'f'
        raise ZeroDivisionError('oops')


@pytest.mark.asyncio
async def test_hook_dispatch(etcd, mocker):
    mocked_entrypoints = functools.partial(
        mock_entrypoints_with_class,
        plugin_cls=[DummyHookPassingPlugin, DummyHookRejectingPlugin, DummyHookErrorPlugin],
    )
    mocker.patch('ai.backend.common.plugin.pkg_resources.iter_entry_points', mocked_entrypoints)
    ctx = HookPluginContext(etcd, {})
    try:
        await ctx.init()

        hook_result = await ctx.dispatch('HOOK1', ('a', 'b'), return_when=FIRST_COMPLETED)
        assert hook_result.status == PASSED
        assert hook_result.result == 1
        assert hook_result.reason is None
        assert hook_result.src_plugin == 'hook-p'

        # If a plugin rejects when set ALL_COMPLETED, only the rejected result is returned.
        hook_result = await ctx.dispatch('HOOK1', ('a', 'b'), return_when=ALL_COMPLETED)
        assert hook_result.status == REJECTED
        assert hook_result.result is None
        assert hook_result.reason == 'dummy rejected 1'
        assert hook_result.src_plugin == 'hook-r'

        # Even when all plguins pass, FIRST_COMPLETED executes only the first successful plugin.
        hook_result = await ctx.dispatch('HOOK2', ('c', 'd'), return_when=FIRST_COMPLETED)
        assert hook_result.status == PASSED
        assert hook_result.result == 2
        assert hook_result.reason is None
        assert hook_result.src_plugin == 'hook-p'

        # For when return_when=ALL_COMPLETED and all plugin succeeds,
        # the caller may map the result returned as a list with src_plugin returned as a list.
        hook_result = await ctx.dispatch('HOOK2', ('c', 'd'), return_when=ALL_COMPLETED)
        assert hook_result.status == PASSED
        assert hook_result.result == [2, 3]
        assert hook_result.reason is None
        assert hook_result.src_plugin == ['hook-p', 'hook-r']

        # If a plugin raises an arbitrary exception other than Reject, it's marked as ERROR.
        hook_result = await ctx.dispatch('HOOK3', ('e', 'f'), return_when=FIRST_COMPLETED)
        assert hook_result.status == ERROR
        assert hook_result.result is None
        assert 'ZeroDivisionError' in hook_result.reason
        assert 'oops' in hook_result.reason
        assert hook_result.src_plugin == 'hook-e'
        hook_result = await ctx.dispatch('HOOK3', ('e', 'f'), return_when=ALL_COMPLETED)
        assert hook_result.status == ERROR
        assert hook_result.result is None
        assert 'ZeroDivisionError' in hook_result.reason
        assert 'oops' in hook_result.reason
        assert hook_result.src_plugin == 'hook-e'
    finally:
        await ctx.cleanup()


@pytest.mark.asyncio
async def test_hook_notify(etcd, mocker):
    mocked_entrypoints = functools.partial(
        mock_entrypoints_with_class,
        plugin_cls=[DummyHookPassingPlugin, DummyHookRejectingPlugin, DummyHookErrorPlugin],
    )
    mocker.patch('ai.backend.common.plugin.pkg_resources.iter_entry_points', mocked_entrypoints)
    ctx = HookPluginContext(etcd, {})
    try:
        await ctx.init()
        # notify() should return successfully no matter a plugin rejects/fails or not.
        hook_result = await ctx.notify('HOOK1', ('a', 'b'))
        assert hook_result is None
        hook_result = await ctx.notify('HOOK2', ('c', 'd'))
        assert hook_result is None
        hook_result = await ctx.notify('HOOK3', ('e', 'f'))
        assert hook_result is None
    finally:
        await ctx.cleanup()
