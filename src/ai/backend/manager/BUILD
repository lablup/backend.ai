python_sources(
    name="src",
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        "src/ai/backend/manager/cli:src",  # not auto-inferred (due to lazy-loading cmdgroup)
        "src/ai/backend/manager/api:src",  # not auto-inferred (due to lazy-loading aiohttp app builder)
        "src/ai/backend/manager/models/alembic:migrations",  # not auto-inferred
        ":resources",
    ],
)

pex_binary(
    name="server",
    dependencies=[
        ":src",
    ],
    entry_point="server.py",
)

pex_binary(
    name="cli",
    dependencies=[
        ":src",
    ],
    entry_point="cli/__main__.py",
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
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
    tags=["wheel"],
)

resource(name="version", source="VERSION")

resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
    ],
)
