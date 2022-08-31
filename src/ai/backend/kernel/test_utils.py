import asynctest


class MockableZMQAsyncSock:

    # Since zmq.Socket/zmq.asyncio.Socket uses a special AttributeSetter mixin which
    # breaks mocking of those instances as-is, we define a dummy socket interface
    # which does not have such side effects.

    @classmethod
    def create_mock(cls):
        return asynctest.Mock(cls())

    def bind(self, addr):
        pass

    def connect(self, addr):
        pass

    def close(self):
        pass

    async def send(self, frame):
        pass

    async def send_multipart(self, msg):
        pass

    async def recv(self):
        pass

    async def recv_multipart(self):
        pass
