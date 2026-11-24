import json
import os
import pkgutil
import subprocess
import sys
from collections.abc import Callable


def modules_loaded_by_cli(load_entry_points: Callable[..., object], package: str) -> set[str]:
    """
    The modules a new interpreter holds after loading the CLI of ``package``.
    This process also holds what the other test files imported.
    """
    result = subprocess.run(
        [
            sys.executable,
            __file__,
            f"{load_entry_points.__module__}:{load_entry_points.__qualname__}",
            package,
        ],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    return set(json.loads(result.stdout))


if __name__ == "__main__":
    pkgutil.resolve_name(sys.argv[1])(allowlist={sys.argv[2]})
    json.dump(sorted(sys.modules), sys.stdout)
