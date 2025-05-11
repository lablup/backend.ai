from .observer import AbstractObserver


class Runner:
    _observers: list[AbstractObserver]
    _closed: bool

    def __init__(self):
        self._observers = []
        self._closed = False

    async def run(self) -> None:
        """
        Run the agent.
        """
        if self._closed:
            raise RuntimeError("Runner is closed.")
        for observer in self._observers:
            await observer.observe()
