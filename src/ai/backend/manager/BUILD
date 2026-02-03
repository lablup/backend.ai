python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/testutils/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/**",
        "!//src/ai/backend/account_manager/**",
        "!//src/ai/backend/web/**",
        "!//src/ai/backend/agent/**",
        "!//src/ai/backend/storage/**",
        "!//src/ai/backend/wsproxy/**",
        "!//src/ai/backend/client/**",
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
            "mgr.start-server": "ai.backend.manager.cli.start_server:main",
        },
        "backendai_scheduler_v10": {
            "fifo": "ai.backend.manager.scheduler.fifo:FIFOSlotScheduler",
            "lifo": "ai.backend.manager.scheduler.fifo:LIFOSlotScheduler",
            "drf": "ai.backend.manager.scheduler.drf:DRFScheduler",
        },
        "backendai_agentselector_v10": {
            "legacy": "ai.backend.manager.scheduler.agent_selector:LegacyAgentSelector",
            "roundrobin": "ai.backend.manager.scheduler.agent_selector:RoundRobinAgentSelector",
            "concentrated": "ai.backend.manager.scheduler.agent_selector:ConcentratedAgentSelector",
            "dispersed": "ai.backend.manager.scheduler.agent_selector:DispersedAgentSelector",
        },
        "backendai_error_monitor_v20": {
            "intrinsic": "ai.backend.manager.plugin.error_monitor:ErrorMonitor",
        },
        "backendai_event_dispatcher_v20": {
            "intrinsic": "ai.backend.manager.plugin.error_monitor:ErrorEventDispatcher",
        },
        "backendai_network_manager_v1": {
            "overlay": "ai.backend.manager.network.overlay:OverlayNetworkPlugin",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

pex_binary(
    name="backendai-manager",
    **common_scie_config("lazy"),
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

pex_binary(
    name="backendai-manager-fat",
    **common_scie_config("eager"),
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-manager*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum"
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
        "**/*.yaml",
        "models/alembic/script.py.mako",
        "models/alembic/revision_history/*.json",
    ],
)
