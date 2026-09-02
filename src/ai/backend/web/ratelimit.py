from aiohttp import web
import logging

log = logging.getLogger(__name__)

@web.middleware
async def proxy_rate_limit_middleware(request: web.Request, handler) -> web.Response:
    # 1. Pass-through for non-/func/ paths
    if not request.path.startswith('/func/'):
        return await handler(request)

    # 2. Pass-through for unauthenticated requests or sessions without user_id
    # Assuming session is populated by a prior auth/session middleware
    session = request.get('session', {})
    user_id = session.get('user_id')
    
    if not user_id:
        return await handler(request)

    rate_limit_client = request.app.get('rate_limit_client')
    if not rate_limit_client:
        log.warning("rate_limit_client not configured in app context")
        return await handler(request)

    # 3. Retrieve published limit for the user
    # Assumes client interface: get_published_limit(user_id) -> dict/object or None
    published_limit = await rate_limit_client.get_published_limit(user_id)
    if not published_limit:
        # Pass-through: No published limit falls back to manager-side limiting
        return await handler(request)

    # 4. Evaluate limit
    # Assumes client interface: evaluate(user_id, published_limit) -> (allowed, remaining, window, limit_val)
    allowed, remaining, window, limit_val = await rate_limit_client.evaluate(user_id, published_limit)

    if not allowed:
        headers = {
            'X-RateLimit-Limit': str(limit_val),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Window': str(window),
        }
        return web.Response(
            status=429,
            text="429: Too Many Requests",
            headers=headers
        )

    return await handler(request)