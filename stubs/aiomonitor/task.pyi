from collections.abc import Callable, Coroutine
from typing import Any

def preserve_termination_log[**P, T](
    corofunc: Callable[P, Coroutine[Any, None, T]],
) -> Callable[P, Coroutine[Any, None, T]]: ...
def __getattr__(name: str) -> Any: ...
