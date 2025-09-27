from __future__ import annotations

import os
import site
import sys
from pathlib import Path


def _reexec_with_argv0(display_name: str) -> None:
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
        # Pass original argv via file to hide strings including "python" in runtime-type and runtime-path.
        args_path = Path(f"/tmp/{os.getpid()}.krunner-args")
        args_path.write_text("\0".join(sys.argv[1:]))
        # "-s" option is to disable user site configurations.
        if mod_name:
            argv = [display_name, "-s", "-m", mod_name]
        else:
            argv = [display_name, "-s", sys.argv[0]]
        venv = os.environ.get("VIRTUAL_ENV", None)
        if venv is None:
            env["PYTHONHOME"] = sys.prefix
        # The process is re-executed in place, overriding argv and cmdline.
        os.execvpe(sys.executable, argv, env)
    else:
        venv = os.environ.get("VIRTUAL_ENV", None)
        os.environ.pop("PYTHONHOME", None)
        if venv is not None:
            venv_sitepkg_path = site.getsitepackages([venv])[0]
            sys.prefix = venv
            sys.path.insert(0, venv_sitepkg_path)


# Prevent being terminated by "pkill -f python" by overriding the cmdline executable name.
# Though, this trick should NOT be used within pytest sessions.
if os.environ.get("PYTEST_VERSION") is None:
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
