python_sources(
    name="src",
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        "src/ai/backend/manager/cli:src",  # not auto-inferred (due to lazy-loading cmdgroup)
        "src/ai/backend/manager/api:src",  # not auto-inferred (due to lazy-loading aiohttp app builder)
        "src/ai/backend/manager/plugin:src",  # not auto-inferred (due to lazy-loading plugins)
        "src/ai/backend/manager/scheduler:src",
        "src/ai/backend/manager/models/alembic:migrations",  # not auto-inferred
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[],
    allowed_dependencies=[
        "//src/ai/backend/common/**",
        "//src/ai/backend/plugin/**",
        "//src/ai/backend/cli/**",
    ],
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

pex_binary(
    name="pex",
    entry_point="ai.backend.cli.__main__",
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

scie_binary(
    name="backendai-manager",
    fat=False,
    dependencies=[":pex"],
    tags=["scie", "lazy"],
)

scie_binary(
    name="backendai-manager-fat",
    fat=True,
    dependencies=[":pex"],
    tags=["scie", "fat"],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-manager-*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum"
        " {} > {}.sha256'"
    ),
    workdir="/dist",
    execution_dependencies=[
        ":backendai-manager",
        ":backendai-manager-fat",
    ],
    tags=["checksum"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="vendor",
    sources=[
        "vendor/*",
        "vendor/**/*",
    ],
)
resources(
    name="resources",
    dependencies=[
        ":version",
        ":vendor",
    ],
    sources=[
        "**/py.typed",
    ],
)
