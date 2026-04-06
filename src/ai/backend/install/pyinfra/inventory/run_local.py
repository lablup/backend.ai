"""
Wrapper to run pyinfra locally on macOS + Python 3.13.

Workaround for gevent's monkey.patch_all() not fully patching subprocess.Popen
in pyinfra's greenlet execution context. The fix patches pyinfra's connectors/util
to use gevent.subprocess directly instead of relying on the monkey-patched stdlib.

See: https://github.com/pyinfra-dev/pyinfra/issues/1652

Usage:
    PYTHONPATH=src python src/ai/backend/install/pyinfra/inventory/run_local.py [--dry] <deploy_script>

Example:
    PYTHONPATH=src python src/ai/backend/install/pyinfra/inventory/run_local.py --dry \
        src/ai/backend/install/pyinfra/deploy/cores/appproxy/coordinator/deploy.py
"""

from __future__ import annotations

import sys

from gevent import monkey

monkey.patch_all()

# Patch pyinfra's connectors/util to use gevent.subprocess directly.
# After monkey.patch_all(), subprocess.Popen should be gevent's version,
# but pyinfra's greenlet execution context triggers a code path where
# CPython's original Popen.__init__ is called instead of gevent's,
# causing _fork_exec (intentionally None in gevent) to be invoked.
# Using gevent.subprocess explicitly avoids this issue.
import pyinfra.connectors.util as _pyinfra_util  # noqa: E402
from gevent.subprocess import PIPE, Popen  # noqa: E402

_pyinfra_util.Popen = Popen
_pyinfra_util.PIPE = PIPE

# Now run pyinfra CLI
from pyinfra_cli.cli import cli  # noqa: E402

sys.exit(cli())
