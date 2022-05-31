from aiohttp import web

from ai.backend.manager.api.utils import method_placeholder
from ai.backend.manager.server import api_middleware


async def test_api_method_override(aiohttp_client):
    observed_method = None
    app = web.Application()

    async def service_handler(request):
        nonlocal observed_method
        observed_method = request.method
        return web.Response(body=b'test')

    app.router.add_route('POST', r'/test',
                         method_placeholder('REPORT'))
    app.router.add_route('REPORT', r'/test',
                         service_handler)
    app.middlewares.append(api_middleware)
    client = await aiohttp_client(app)

    # native method
    resp = await client.request('REPORT', '/test')
    assert resp.status == 200
    assert (await resp.read()) == b'test'
    assert observed_method == 'REPORT'

    # overriden method
    observed_method = None
    resp = await client.post('/test', headers={
        'X-Method-Override': 'REPORT',
    })
    assert resp.status == 200
    assert (await resp.read()) == b'test'
    assert observed_method == 'REPORT'

    # calling placeholder
    observed_method = None
    resp = await client.post('/test')
    assert resp.status == 405
    assert observed_method is None

    # calling with non-relevant method
    observed_method = None
    resp = await client.delete('/test')
    assert resp.status == 405
    assert observed_method is None


async def test_api_method_override_with_different_ops(aiohttp_client):
    observed_method = None
    app = web.Application()

    async def op1_handler(request):
        nonlocal observed_method
        observed_method = request.method
        return web.Response(body=b'op1')

    async def op2_handler(request):
        nonlocal observed_method
        observed_method = request.method
        return web.Response(body=b'op2')

    app.router.add_route('POST', r'/test', op1_handler)
    app.router.add_route('REPORT', r'/test', op2_handler)
    app.middlewares.append(api_middleware)
    client = await aiohttp_client(app)

    # native method
    resp = await client.request('POST', '/test')
    assert resp.status == 200
    assert (await resp.read()) == b'op1'
    assert observed_method == 'POST'

    # native method
    observed_method = None
    resp = await client.request('REPORT', '/test')
    assert resp.status == 200
    assert (await resp.read()) == b'op2'
    assert observed_method == 'REPORT'

    # overriden method
    observed_method = None
    resp = await client.request('REPORT', '/test', headers={
        'X-Method-Override': 'POST',
    })
    assert resp.status == 200
    assert (await resp.read()) == b'op1'
    assert observed_method == 'POST'

    # overriden method
    observed_method = None
    resp = await client.request('POST', '/test', headers={
        'X-Method-Override': 'REPORT',
    })
    assert resp.status == 200
    assert (await resp.read()) == b'op2'
    assert observed_method == 'REPORT'


async def test_api_ver(aiohttp_client):
    inner_request = None
    app = web.Application()

    async def dummy_handler(request):
        nonlocal inner_request
        inner_request = request
        return web.Response(body=b'test')

    app.router.add_post(r'/test', dummy_handler)
    app.middlewares.append(api_middleware)
    client = await aiohttp_client(app)

    # normal call
    resp = await client.post('/test', headers={
        'X-BackendAI-Version': 'v5.20191215',
    })
    assert resp.status == 200
    assert inner_request['api_version'][0] == 5

    # normal call with different version
    resp = await client.post('/test', headers={
        'X-BackendAI-Version': 'v4.20190615',
    })
    assert resp.status == 200
    assert inner_request['api_version'][0] == 4

    # calling with invalid/deprecated version
    resp = await client.post('/test', headers={
        'X-BackendAI-Version': 'v2.20170315',
    })
    assert resp.status == 400
    assert 'Unsupported' in (await resp.json())['msg']
