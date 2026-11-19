"""Give each pytest-xdist worker its own `BACKEND_TEST_EXEC_SLOT`, as Pants does per process.

Loaded with `-p xdist_slot` before any test module reads the slot.
"""

from __future__ import annotations

import os

_worker = os.environ.get("PYTEST_XDIST_WORKER", "")
if _worker.startswith("gw"):
    os.environ["BACKEND_TEST_EXEC_SLOT"] = _worker[2:]
