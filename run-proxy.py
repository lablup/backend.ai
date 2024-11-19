from datetime import datetime
from ai.backend.client.auth import generate_signature
from dateutil.tz import tzutc
from aiohttp import web, ClientSession
import yarl

async def proxy_handler(request):
    print('Received request')

    auth_header = request.headers.get('Authorization')
    print('auth_header!', auth_header)

    # Validate the request
    # TODO: Compare the auth header value with the value specified in the policy.
    if not auth_header:
        return web.Response(status=401)

    date = datetime.now(tzutc())
    api_version = 'v8.20240915'
    manager_endpoint = 'http://localhost:8091'
    rel_url = 'container-registries/webhook'

    hdrs, _ = generate_signature(
        method='POST',
        version=api_version,
        endpoint=yarl.URL(manager_endpoint),
        date=date,
        rel_url=f"/{rel_url}",
        content_type='application/octet-stream',
        access_key='AKIAIOSFODNN7EXAMPLE',
        secret_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        hash_type='sha256',
    )

    hdrs.update({
        'Date': date.isoformat(),
        'X-BackendAI-Version': api_version,
    })

    async with ClientSession() as session:
        async with session.post(f'{manager_endpoint}/{rel_url}', data=await request.read(), headers=hdrs) as resp:
            return web.Response(status=resp.status, body=await resp.read())

app = web.Application()
app.router.add_post('/harbor-webhook', proxy_handler)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=60400)