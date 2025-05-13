class PortPool:
    _port_pool: set[int]

    def __init__(self, start: int, end: int) -> None:
        self._port_pool = set(range(start, end + 1))

    def acquire(self) -> int:
        return self._port_pool.pop()

    def release(self, port: int) -> None:
        self._port_pool.add(port)
