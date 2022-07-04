import asyncio
import tracemalloc

tracemalloc.start()
import grpc


async def main():
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    for stat in top_stats:
        if 'test.py:15' in str(stat):
            print(stat)
    ssl_cred = grpc.ssl_channel_credentials()
    token = 'abcd' * 100000
    token_cred = grpc.access_token_call_credentials(token)
    composite_cred = grpc.composite_channel_credentials(ssl_cred, token_cred)
    chan = grpc.aio.secure_channel('host', composite_cred)
    await chan._close(None)

    # del chan, composite_cred, token_cred, token
    # gc.collect()


while True:
    asyncio.run(main())
