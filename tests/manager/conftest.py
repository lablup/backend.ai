import asyncio
import hashlib, hmac
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import (
    Any,
    AsyncContextManager,
    AsyncIterator,
    Iterator,
    List,
    Mapping,
    Sequence,
    Tuple,
    Type,
)
from unittest.mock import MagicMock, AsyncMock
from urllib.parse import quote_plus as urlquote

import aiohttp
from aiohttp import web
from dateutil.tz import tzutc
import sqlalchemy as sa
import pytest
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.config import redis_config_iv
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import HostPortPair
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.config import LocalConfig, SharedConfig, load as load_config
from ai.backend.manager.server import (
    build_root_app,
)
from ai.backend.manager.api.types import (
    CleanupContext,
)
from ai.backend.manager.models.base import populate_fixture, pgsql_connect_opts
from ai.backend.manager.models import (
    scaling_groups,
    agents,
    kernels, keypairs, vfolders,
)
from ai.backend.manager.models.utils import connect_database
from ai.backend.manager.registry import AgentRegistry

here = Path(__file__).parent


@pytest.fixture(scope='session', autouse=True)
def test_id():
    return secrets.token_hex(12)


@pytest.fixture(scope='session', autouse=True)
def test_ns(test_id):
    ret = f'testing-ns-{test_id}'
    os.environ['BACKEND_NAMESPACE'] = ret
    return ret


@pytest.fixture(scope='session')
def test_db(test_id):
    return f'test_db_{test_id}'


@pytest.fixture(scope='session')
def vfolder_mount(test_id):
    ret = Path(f'/tmp/backend.ai-testing/vfolders-{test_id}')
    ret.mkdir(parents=True, exist_ok=True)
    yield ret
    shutil.rmtree(ret.parent)


@pytest.fixture(scope='session')
def vfolder_fsprefix(test_id):
    # NOTE: the prefix must NOT start with "/"
    return Path('fsprefix/inner/')


@pytest.fixture(scope='session')
def vfolder_host():
    return 'local'


@pytest.fixture(scope='session')
def local_config(test_id, test_db) -> Iterator[LocalConfig]:
    cfg = load_config()
    assert isinstance(cfg, LocalConfig)
    cfg['db']['name'] = test_db
    cfg['manager']['num-proc'] = 1
    ipc_base_path = Path(f'/tmp/backend.ai/manager-testing/ipc-{test_id}')
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    cfg['manager']['ipc-base-path'] = ipc_base_path
    cfg['manager']['distributed-lock'] = 'filelock'
    cfg['manager']['service-addr'] = HostPortPair('127.0.0.1', 29100)
    # In normal setups, this is read from etcd.
    cfg['redis'] = redis_config_iv.check({
        'addr': {'host': '127.0.0.1', 'port': '6379'},
    })
    yield cfg
    shutil.rmtree(ipc_base_path)


@pytest.fixture(scope='session')
def etcd_fixture(test_id, local_config, vfolder_mount, vfolder_fsprefix, vfolder_host) -> Iterator[None]:
    # Clear and reset etcd namespace using CLI functions.
    print("NOTE: This test suite uses a local Redis daemon running at 127.0.0.1:6379!", file=sys.stderr)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.etcd.json') as f:
        etcd_fixture = {
            'volumes': {
                '_mount': str(vfolder_mount),
                '_fsprefix': str(vfolder_fsprefix),
                '_default_host': str(vfolder_host),
            },
            'nodes': {
            },
            'config': {
                'docker': {
                    'registry': {
                        'cr.backend.ai': {
                            '': 'https://cr.backend.ai',
                            'type': 'harbor2',
                            'project': 'stable',
                        },
                    },
                },
                'redis': {
                    'addr': '127.0.0.1:6379',
                },
                'plugins': {
                    'cloudia': {
                        'base_url': '127.0.0.1:8090',
                        'user': 'fake-cloudia-user@lablup.com',
                        'password': 'fake-password',
                    },
                },
            },
        }
        json.dump(etcd_fixture, f)
        f.flush()
        subprocess.call([
            sys.executable,
            '-m', 'ai.backend.manager.cli',
            'etcd', 'put-json', '', f.name,
        ])
    yield
    subprocess.call([
        sys.executable,
        '-m', 'ai.backend.manager.cli',
        'etcd', 'delete',
        '--prefix', '',
    ])


@pytest.fixture
async def shared_config(app, etcd_fixture):
    root_ctx: RootContext = app['_root.context']
    shared_config = SharedConfig(
        root_ctx.local_config['etcd']['addr'],
        root_ctx.local_config['etcd']['user'],
        root_ctx.local_config['etcd']['password'],
        root_ctx.local_config['etcd']['namespace'],
    )
    await shared_config.reload()
    root_ctx: RootContext = app['_root.context']
    root_ctx.shared_config = shared_config
    yield shared_config


@pytest.fixture(scope='session')
def database(request, local_config, test_db):
    """
    Create a new database for the current test session
    and install the table schema using alembic.
    """
    db_addr = local_config['db']['addr']
    db_user = local_config['db']['user']
    db_pass = local_config['db']['password']

    # Create database using low-level psycopg2 API.
    # Temporarily use "testing" dbname until we create our own db.
    if db_pass:
        db_url = f'postgresql+asyncpg://{urlquote(db_user)}:{urlquote(db_pass)}@{db_addr}/testing'
    else:
        db_url = f'postgresql+asyncpg://{urlquote(db_user)}@{db_addr}/testing'

    async def init_db():
        engine = sa.ext.asyncio.create_async_engine(
            db_url,
            connect_args=pgsql_connect_opts,
            isolation_level="AUTOCOMMIT",
        )
        async with engine.connect() as conn:
            await conn.execute(sa.text(f'CREATE DATABASE "{test_db}";'))
        await engine.dispose()

    asyncio.run(init_db())

    async def finalize_db():
        engine = sa.ext.asyncio.create_async_engine(
            db_url,
            connect_args=pgsql_connect_opts,
            isolation_level="AUTOCOMMIT",
        )
        async with engine.connect() as conn:
            await conn.execute(sa.text(f'REVOKE CONNECT ON DATABASE "{test_db}" FROM public;'))
            await conn.execute(sa.text('SELECT pg_terminate_backend(pid) FROM pg_stat_activity '
                               'WHERE pid <> pg_backend_pid();'))
            await conn.execute(sa.text(f'DROP DATABASE "{test_db}";'))
        await engine.dispose()

    request.addfinalizer(lambda: asyncio.run(finalize_db()))

    # Load the database schema using CLI function.
    alembic_url = f'postgresql://{db_user}:{db_pass}@{db_addr}/{test_db}'
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf8') as alembic_cfg:
        alembic_sample_cfg = here / '..' / 'alembic.ini.sample'
        alembic_cfg_data = alembic_sample_cfg.read_text()
        alembic_cfg_data = re.sub(
            r'^sqlalchemy.url = .*$',
            f'sqlalchemy.url = {alembic_url}',
            alembic_cfg_data, flags=re.M)
        alembic_cfg.write(alembic_cfg_data)
        alembic_cfg.flush()
        subprocess.call([
            'python', '-m', 'ai.backend.manager.cli',
            'schema', 'oneshot',
            '-f', alembic_cfg.name,
        ])


@pytest.fixture()
async def database_engine(local_config, database):
    async with connect_database(local_config) as db:
        yield db


@pytest.fixture()
def database_fixture(local_config, test_db, database):
    """
    Populate the example data as fixtures to the database
    and delete them after use.
    """
    db_addr = local_config['db']['addr']
    db_user = local_config['db']['user']
    db_pass = local_config['db']['password']
    db_url = f'postgresql+asyncpg://{db_user}:{urlquote(db_pass)}@{db_addr}/{test_db}'

    fixtures = {}
    # NOTE: The fixtures must be loaded in the order that they are present.
    #       Normal dicts on Python 3.6 or later guarantees the update ordering.
    fixtures.update(json.loads(
        (Path(__file__).parent.parent /
         'fixtures' / 'example-keypairs.json').read_text(),
    ))
    fixtures.update(json.loads(
        (Path(__file__).parent.parent /
         'fixtures' / 'example-resource-presets.json').read_text(),
    ))

    async def init_fixture():
        engine: SAEngine = sa.ext.asyncio.create_async_engine(
            db_url,
            connect_args=pgsql_connect_opts,
        )
        try:
            await populate_fixture(engine, fixtures)
        finally:
            await engine.dispose()

    asyncio.run(init_fixture())

    yield

    async def clean_fixture():
        engine: SAEngine = sa.ext.asyncio.create_async_engine(
            db_url,
            connect_args=pgsql_connect_opts,
        )
        try:
            async with engine.begin() as conn:
                await conn.execute((vfolders.delete()))
                await conn.execute((kernels.delete()))
                await conn.execute((agents.delete()))
                await conn.execute((keypairs.delete()))
                await conn.execute((scaling_groups.delete()))
        finally:
            await engine.dispose()

    asyncio.run(clean_fixture())


@pytest.fixture
def file_lock_factory(local_config, request):
    from ai.backend.common.lock import FileLock

    def _make_lock(lock_id):
        lock_path = local_config['manager']['ipc-base-path'] / f'testing.{lock_id}.lock'
        lock = FileLock(lock_path, timeout=0)
        request.addfinalizer(partial(lock_path.unlink, missing_ok=True))
        return lock

    return _make_lock


class Client:
    def __init__(self, session: aiohttp.ClientSession, url) -> None:
        self._session = session
        if not url.endswith('/'):
            url += '/'
        self._url = url

    def request(self, method, path, **kwargs):
        while path.startswith('/'):
            path = path[1:]
        url = self._url + path
        return self._session.request(method, url, **kwargs)

    def get(self, path, **kwargs):
        while path.startswith('/'):
            path = path[1:]
        url = self._url + path
        return self._session.get(url, **kwargs)

    def post(self, path, **kwargs):
        while path.startswith('/'):
            path = path[1:]
        url = self._url + path
        return self._session.post(url, **kwargs)

    def put(self, path, **kwargs):
        while path.startswith('/'):
            path = path[1:]
        url = self._url + path
        return self._session.put(url, **kwargs)

    def patch(self, path, **kwargs):
        while path.startswith('/'):
            path = path[1:]
        url = self._url + path
        return self._session.patch(url, **kwargs)

    def delete(self, path, **kwargs):
        while path.startswith('/'):
            path = path[1:]
        url = self._url + path
        return self._session.delete(url, **kwargs)

    def ws_connect(self, path, **kwargs):
        while path.startswith('/'):
            path = path[1:]
        url = self._url + path
        return self._session.ws_connect(url, **kwargs)


@pytest.fixture
async def app(local_config, event_loop):
    """
    Create an empty application with the test configuration.
    """
    return build_root_app(
        0,
        local_config,
        cleanup_contexts=[],
        subapp_pkgs=[],
    )


@pytest.fixture
async def create_app_and_client(local_config, event_loop) -> AsyncIterator:
    client: Client | None = None
    client_session: aiohttp.ClientSession | None = None
    runner: web.BaseRunner | None = None
    _outer_ctxs: List[AsyncContextManager] = []

    async def app_builder(
        cleanup_contexts: Sequence[CleanupContext] = None,
        subapp_pkgs: Sequence[str] = None,
        scheduler_opts: Mapping[str, Any] = None,
    ) -> Tuple[web.Application, Client]:
        nonlocal client, client_session, runner
        nonlocal _outer_ctxs

        if scheduler_opts is None:
            scheduler_opts = {}
        _cleanup_ctxs = []
        _outer_ctx_classes: List[Type[AsyncContextManager]] = []
        if cleanup_contexts is not None:
            for ctx in cleanup_contexts:
                # if isinstance(ctx, AsyncContextManager):
                if ctx.__name__ in ['shared_config_ctx', 'webapp_plugins_ctx']:
                    _outer_ctx_classes.append(ctx)  # type: ignore
                else:
                    _cleanup_ctxs.append(ctx)
        app = build_root_app(
            0,
            local_config,
            cleanup_contexts=_cleanup_ctxs,
            subapp_pkgs=subapp_pkgs,
            scheduler_opts={
                'close_timeout': 10,
                **scheduler_opts,
            },
        )
        root_ctx: RootContext = app['_root.context']
        for octx_cls in _outer_ctx_classes:
            octx = octx_cls(root_ctx)  # type: ignore
            _outer_ctxs.append(octx)
            await octx.__aenter__()
        runner = web.AppRunner(app, handle_signals=False)
        await runner.setup()
        site = web.TCPSite(
            runner,
            str(root_ctx.local_config['manager']['service-addr'].host),
            root_ctx.local_config['manager']['service-addr'].port,
            reuse_port=True,
        )
        await site.start()
        port = root_ctx.local_config['manager']['service-addr'].port
        client_session = aiohttp.ClientSession()
        client = Client(client_session, f'http://127.0.0.1:{port}')
        return app, client

    yield app_builder

    if client_session is not None:
        await client_session.close()
    if runner is not None:
        await runner.cleanup()
    for octx in reversed(_outer_ctxs):
        await octx.__aexit__(None, None, None)


@pytest.fixture
def default_keypair():
    return {
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    }


@pytest.fixture
def default_domain_keypair():
    """Default domain admin keypair"""
    return {
        'access_key': 'AKIAHUKCHDEZGEXAMPLE',
        'secret_key': 'cWbsM_vBB4CzTW7JdORRMx8SjGI3-wEXAMPLEKEY',
    }


@pytest.fixture
def user_keypair():
    return {
        'access_key': 'AKIANABBDUSEREXAMPLE',
        'secret_key': 'C8qnIo29EZvXkPK_MXcuAakYTy4NYrxwmCEyNPlf',
    }


@pytest.fixture
def monitor_keypair():
    return {
        'access_key': 'AKIANAMONITOREXAMPLE',
        'secret_key': '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',
    }


@pytest.fixture
def get_headers(app, default_keypair):
    def create_header(
        method,
        url,
        req_bytes,
        ctype='application/json',
        hash_type='sha256',
        api_version='v5.20191215',
        keypair=default_keypair,
    ) -> dict[str, str]:
        now = datetime.now(tzutc())
        root_ctx: RootContext = app['_root.context']
        hostname = f"127.0.0.1:{root_ctx.local_config['manager']['service-addr'].port}"
        headers = {
            'Date': now.isoformat(),
            'Content-Type': ctype,
            'Content-Length': str(len(req_bytes)),
            'X-BackendAI-Version': api_version,
        }
        if api_version >= 'v4.20181215':
            req_bytes = b''
        else:
            if ctype.startswith('multipart'):
                req_bytes = b''
        if ctype.startswith('multipart'):
            # Let aiohttp to create appropriate header values
            # (e.g., multipart content-type header with message boundaries)
            del headers['Content-Type']
            del headers['Content-Length']
        req_hash = hashlib.new(hash_type, req_bytes).hexdigest()
        sign_bytes = method.upper().encode() + b'\n' \
                     + url.encode() + b'\n' \
                     + now.isoformat().encode() + b'\n' \
                     + b'host:' + hostname.encode() + b'\n' \
                     + b'content-type:' + ctype.encode() + b'\n' \
                     + b'x-backendai-version:' + api_version.encode() + b'\n' \
                     + req_hash.encode()
        sign_key = hmac.new(keypair['secret_key'].encode(),
                            now.strftime('%Y%m%d').encode(), hash_type).digest()
        sign_key = hmac.new(sign_key, hostname.encode(), hash_type).digest()
        signature = hmac.new(sign_key, sign_bytes, hash_type).hexdigest()
        headers['Authorization'] = \
            f'BackendAI signMethod=HMAC-{hash_type.upper()}, ' \
            + f'credential={keypair["access_key"]}:{signature}'
        return headers
    return create_header


@pytest.fixture
async def prepare_kernel(request, create_app_and_client,
                         get_headers, default_keypair):
    sess_id = f'test-kernel-session-{secrets.token_hex(8)}'
    app, client = await create_app_and_client(
        modules=['etcd', 'events', 'auth', 'vfolder',
                 'admin', 'ratelimit', 'kernel', 'stream', 'manager'],
        spawn_agent=True)
    root_ctx: RootContext = app['_root.context']

    async def create_kernel(image='lua:5.3-alpine', tag=None):
        url = '/v3/kernel/'
        req_bytes = json.dumps({
            'image': image,
            'tag': tag,
            'clientSessionToken': sess_id,
        }).encode()
        headers = get_headers('POST', url, req_bytes)
        response = await client.post(url, data=req_bytes, headers=headers)
        return await response.json()

    yield app, client, create_kernel

    access_key = default_keypair['access_key']
    try:
        await root_ctx.registry.destroy_session(sess_id, access_key)
    except Exception:
        pass


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}


@pytest.fixture
async def registry_ctx(mocker):
    mock_shared_config = MagicMock()
    mock_shared_config.update_resource_slots = AsyncMock()
    mock_shared_config.etcd = None
    mock_db = MagicMock()
    mock_dbconn = MagicMock()
    mock_dbconn_ctx = MagicMock()
    mock_dbresult = MagicMock()
    mock_dbresult.rowcount = 1
    mock_db.connect = MagicMock(return_value=mock_dbconn_ctx)
    mock_db.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_dbconn_ctx.__aenter__ = AsyncMock(return_value=mock_dbconn)
    mock_dbconn_ctx.__aexit__ = AsyncMock()
    mock_dbconn.execute = AsyncMock(return_value=mock_dbresult)
    mock_dbconn.begin = MagicMock(return_value=mock_dbconn_ctx)
    mock_redis_stat = MagicMock()
    mock_redis_live = MagicMock()
    mock_redis_live.hset = AsyncMock()
    mock_redis_image = MagicMock()
    mock_event_dispatcher = MagicMock()
    mock_event_producer = MagicMock()
    mock_event_producer.produce_event = AsyncMock()
    mocked_etcd = DummyEtcd()
    # mocker.object.patch(mocked_etcd, 'get_prefix', AsyncMock(return_value={}))
    hook_plugin_ctx = HookPluginContext(mocked_etcd, {})  # type: ignore

    registry = AgentRegistry(
        shared_config=mock_shared_config,
        db=mock_db,
        redis_stat=mock_redis_stat,
        redis_live=mock_redis_live,
        redis_image=mock_redis_image,
        event_dispatcher=mock_event_dispatcher,
        event_producer=mock_event_producer,
        storage_manager=None,  # type: ignore
        hook_plugin_ctx=hook_plugin_ctx,
    )
    await registry.init()
    try:
        yield (
            registry,
            mock_dbconn,
            mock_dbresult,
            mock_shared_config,
            mock_event_dispatcher,
            mock_event_producer,
        )
    finally:
        await registry.shutdown()
