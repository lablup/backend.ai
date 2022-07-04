import tempfile
import textwrap as tw
from pathlib import Path

from ai.backend.plugin.entrypoint import (
    extract_entrypoints_from_buildscript,
    match_blocklist,
)


def test_parse_build():
    with tempfile.NamedTemporaryFile('w') as f:
        f.write(tw.dedent('''
            python_sources(
                name="lib",
            )
            python_distribution(
                name="dist",
                dependencies=[
                    ":service",
                ],
                provides=python_artifact(
                    name="backend.ai-manager",
                    description="Backend.AI Manager",
                    license="LGPLv3",
                ),
                entry_points={
                    "backendai_cli_v10": {
                        "mgr": "ai.backend.manager.cli.__main__:main",
                        "mgr.start-server": "ai.backend.manager.server:main",
                    },
                    "backendai_scheduler_v10": {
                        "fifo": "ai.backend.manager.scheduler.fifo:FIFOSlotScheduler",
                        "lifo": "ai.backend.manager.scheduler.fifo:LIFOSlotScheduler",
                        "drf": "ai.backend.manager.scheduler.drf:DRFScheduler",
                        "mof": "ai.backend.manager.scheduler.mof:MOFScheduler",
                    },
                    "backendai_error_monitor_v20": {
                        "intrinsic": "ai.backend.manager.plugin.error_monitor:ErrorMonitor",
                    },
                },
                generate_setup=True,
            )
            python_tests(
                name="tests",
            )
        '''))
        f.flush()
        p = Path(f.name)
        items = [*extract_entrypoints_from_buildscript("backendai_cli_v10", p)]
        assert (items[0].name, items[0].module, items[0].attr) == \
               ("mgr", "ai.backend.manager.cli.__main__", "main")
        assert (items[1].name, items[1].module, items[1].attr) == \
               ("mgr.start-server", "ai.backend.manager.server", "main")
        items = [*extract_entrypoints_from_buildscript("backendai_scheduler_v10", p)]
        assert (items[0].name, items[0].module, items[0].attr) == \
               ("fifo", "ai.backend.manager.scheduler.fifo", "FIFOSlotScheduler")
        assert (items[1].name, items[1].module, items[1].attr) == \
               ("lifo", "ai.backend.manager.scheduler.fifo", "LIFOSlotScheduler")
        assert (items[2].name, items[2].module, items[2].attr) == \
               ("drf", "ai.backend.manager.scheduler.drf", "DRFScheduler")
        assert (items[3].name, items[3].module, items[3].attr) == \
               ("mof", "ai.backend.manager.scheduler.mof", "MOFScheduler")
        items = [*extract_entrypoints_from_buildscript("backendai_error_monitor_v20", p)]
        assert (items[0].name, items[0].module, items[0].attr) == \
               ("intrinsic", "ai.backend.manager.plugin.error_monitor", "ErrorMonitor")


def test_match_blocklist():
    assert match_blocklist("ai.backend.manager:abc", {"ai.backend.manager"})
    assert not match_blocklist("ai.backend.manager:abc", {"ai.backend.agent"})
    assert match_blocklist("ai.backend.manager.scheduler.fifo:FIFOScheduler", {"ai.backend.manager"})
    assert not match_blocklist("ai.backend.common.monitor:ErrorMonitor", {"ai.backend.manager"})
