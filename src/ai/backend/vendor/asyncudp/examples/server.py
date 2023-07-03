import asyncio
import asyncudp


async def main():
    sock = await asyncudp.create_socket(local_addr=('127.0.0.1', 9999))

    while True:
        data, addr = await sock.recvfrom()
        print(data, addr)
        sock.sendto(data, addr)


asyncio.run(main())
