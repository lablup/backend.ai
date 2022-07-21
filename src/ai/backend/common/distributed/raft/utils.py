import threading


class AtomicInteger:
    def __init__(self, value: int = 0):
        self._value = value
        self._lock = threading.Lock()

    def increase(self):
        with self._lock:
            self._value += 1

    def decrease(self):
        with self._lock:
            self._value -= 1

    def set(self, value: int = 0):
        with self._lock:
            self._value = value

    @property
    def value(self) -> int:
        return self._value
