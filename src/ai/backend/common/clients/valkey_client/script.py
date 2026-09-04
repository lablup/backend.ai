from collections.abc import Callable
from typing import Final, cast

from glide import Script

# glide ships `py.typed` but leaves `Script.__init__` unannotated, so calling the class
# directly fails the `no-untyped-call` check. Drop this once upstream annotates it.
_new_script: Final[Callable[[str], Script]] = cast(Callable[[str], Script], Script)


def create_script(code: str) -> Script:
    """Compile a Lua script for `invoke_script`."""
    return _new_script(code)
