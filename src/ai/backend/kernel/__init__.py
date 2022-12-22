from .base import BaseRunner
from .terminal import Terminal

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
