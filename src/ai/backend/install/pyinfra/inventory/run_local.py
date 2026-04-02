"""
Wrapper to run pyinfra locally with gevent subprocess fix for macOS + Python 3.13.

Usage:
    PYTHONPATH=src python src/ai/backend/install/pyinfra/inventory/run_local.py [--dry] <deploy_script>

Example:
    PYTHONPATH=src python src/ai/backend/install/pyinfra/inventory/run_local.py --dry \
        src/ai/backend/install/pyinfra/deploy/cores/appproxy/coordinator/deploy.py
"""

from __future__ import annotations

import subprocess
import sys

# Save _fork_exec before gevent monkey-patches it to None (macOS + Python 3.13 bug)
# https://github.com/gevent/gevent/issues/2169
_original_fork_exec = subprocess._fork_exec

from gevent import monkey  # noqa: E402

monkey.patch_all()

# Restore _fork_exec after monkey patching
subprocess._fork_exec = _original_fork_exec

# Now run pyinfra CLI
from pyinfra_cli.cli import cli  # noqa: E402

sys.exit(cli())
