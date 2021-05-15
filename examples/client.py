import asyncio
import asyncudp


async def main():
    sock = await asyncudp.create_socket(remote_addr=('127.0.0.1', 9999))
    sock.sendto(b'Hello!')
    print(await sock.recvfrom())
    sock.close()


asyncio.run(main())
