import os
import sys
from pathlib import Path


def _sitepkg_version() -> str:
    version = sys.version_info
    if hasattr(sys, "abiflags") and "t" in sys.abiflags:
        abi_thread = "t"
    else:
        abi_thread = ""
    return f"python{version[0]}.{version[1]}{abi_thread}"


def _reexec_with_argv0(argv0: str) -> None:
    if os.environ.get("BACKEND_REEXECED") != "1":
        env = os.environ.copy()
        env["BACKEND_REEXECED"] = "1"
        mod_name = None
        try:
            spec = globals().get("__spec__")
            if spec and getattr(spec, "name", None):
                mod_name = spec.name
        except Exception:
            pass
        argv1 = sys.argv[1]
        # Prevent being terminated by "pkill -f python" by aliasing the runtime-type argument.
        if argv1 == "python":
            argv1 = "default"
        # "-s" option is to disable user site configurations.
        if mod_name:
            argv = [argv0, "-s", "-m", mod_name, argv1] + sys.argv[2:]
        else:
            argv = [argv0, "-s", sys.argv[0], argv1] + sys.argv[2:]
        os.execvpe(sys.executable, argv, env)
    else:
        venv = os.environ.get("VIRTUAL_ENV", None)
        if venv is not None:
            sys.prefix = venv
            sys.path.insert(0, str(Path(venv) / "lib" / _sitepkg_version() / "site-packages"))


# Prevent being terminated by "pkill -f python" by overriding the cmdline executable name.
_reexec_with_argv0("bai-krunner")


# The above reexec function must run before ANY import!
from .base import BaseRunner  # noqa: E402
from .terminal import Terminal  # noqa: E402

__all__ = (
    "BaseRunner",
    "Terminal",
    "lang_map",
)

lang_map = {
    "app": "ai.backend.kernel.app.Runner",
    "python": "ai.backend.kernel.python.Runner",
    "default": "ai.backend.kernel.python.Runner",
    "c": "ai.backend.kernel.c.Runner",
    "cpp": "ai.backend.kernel.cpp.Runner",
    "golang": "ai.backend.kernel.golang.Runner",
    "rust": "ai.backend.kernel.rust.Runner",
    "java": "ai.backend.kernel.java.Runner",
    "haskell": "ai.backend.kernel.haskell.Runner",
    "julia": "ai.backend.kernel.julia.Runner",
    "lua": "ai.backend.kernel.lua.Runner",
    "nodejs": "ai.backend.kernel.nodejs.Runner",
    "octave": "ai.backend.kernel.octave.Runner",
    "php": "ai.backend.kernel.php.Runner",
    "r": "ai.backend.kernel.r.Runner",
    "scheme": "ai.backend.kernel.scheme.Runner",
    "git": "ai.backend.kernel.git.Runner",
    "vendor.aws_polly": "ai.backend.kernel.vendor.aws_polly.Runner",
    "vendor.h2o": "ai.backend.kernel.vendor.h2o.Runner",
}
