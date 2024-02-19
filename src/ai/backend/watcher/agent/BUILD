python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-agent-watcher",
        description="Backend.AI Agent Watcher plugin",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_watcher_v10": {
            "agent": "ai.backend.watcher_modules.agent.watcher:AgentWatcherPlugin",
        },
        "backendai_watcher_webapp_v10": {
            "agent": "ai.backend.watcher_modules.agent.webapp:AgentWatcherWebapp",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
    ],
)
