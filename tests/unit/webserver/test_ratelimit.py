import pytest
from unittest.mock import AsyncMock
from aiohttp import web
from src.ai.backend.web.ratelimit import proxy_rate_limit_middleware

@pytest.fixture
def rate_limit_client_mock():
    mock = AsyncMock()
    return mock

@pytest.fixture
def app(rate_limit_client_mock):
    app = web.Application()
    app['rate_limit_client'] = rate_limit_client_mock
    return app

@pytest.fixture
def make_request(app):
    def _make_request(path, user_id=None):
        req = AsyncMock(spec=web.Request)
        req.path = path
        req.app = app
        req.get.return_value = {'user_id': user_id} if user_id else {}
        return req
    return _make_request

@pytest.fixture
def handler_mock():
    async def _handler(request):
        return web.Response(status=200, text="OK")
    return _handler

@pytest.mark.asyncio
async def test_pass_through_non_func_path(make_request, handler_mock, rate_limit_client_mock):
    req = make_request('/api/health', user_id='user_123')
    
    resp = await proxy_rate_limit_middleware(req, handler_mock)
    
    assert resp.status == 200
    rate_limit_client_mock.get_published_limit.assert_not_called()

@pytest.mark.asyncio
async def test_pass_through_unauthenticated(make_request, handler_mock, rate_limit_client_mock):
    req = make_request('/func/proxy', user_id=None)
    
    resp = await proxy_rate_limit_middleware(req, handler_mock)
    
    assert resp.status == 200
    rate_limit_client_mock.get_published_limit.assert_not_called()

@pytest.mark.asyncio
async def test_pass_through_missing_published_limit(make_request, handler_mock, rate_limit_client_mock):
    req = make_request('/func/proxy', user_id='user_123')
    rate_limit_client_mock.get_published_limit.return_value = None
    
    resp = await proxy_rate_limit_middleware(req, handler_mock)
    
    assert resp.status == 200
    rate_limit_client_mock.evaluate.assert_not_called()

@pytest.mark.asyncio
async def test_request_within_limit_proxied(make_request, handler_mock, rate_limit_client_mock):
    req = make_request('/func/proxy', user_id='user_123')
    rate_limit_client_mock.get_published_limit.return_value = {'limit': 100}
    # (allowed, remaining, window, limit_val)
    rate_limit_client_mock.evaluate.return_value = (True, 99, 60, 100)
    
    resp = await proxy_rate_limit_middleware(req, handler_mock)
    
    assert resp.status == 200

@pytest.mark.asyncio
async def test_request_exceeds_limit_returns_429(make_request, handler_mock, rate_limit_client_mock):
    req = make_request('/func/proxy', user_id='user_123')
    rate_limit_client_mock.get_published_limit.return_value = {'limit': 100}
    # (allowed, remaining, window, limit_val)
    rate_limit_client_mock.evaluate.return_value = (False, 0, 30, 100)
    
    resp = await proxy_rate_limit_middleware(req, handler_mock)
    
    assert resp.status == 429
    assert resp.headers.get('X-RateLimit-Limit') == '100'
    assert resp.headers.get('X-RateLimit-Remaining') == '0'
    assert resp.headers.get('X-RateLimit-Window') == '30'