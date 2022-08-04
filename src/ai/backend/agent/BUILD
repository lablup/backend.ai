python_sources(
    name="src",
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        "src/ai/backend/agent/docker:src",  # not auto-inferred
        "src/ai/backend/agent/kubernetes:src",  # not auto-inferred
        "src/ai/backend/runner:src",
        "src/ai/backend/helpers:src",
        "src/ai/backend/kernel:src",
        "//:reqs#backend.ai-krunner-static-gnu",  # not auto-inferred
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
    name="watcher",
    entry_point="watcher.py",
)

python_requirement(
    name="kernel-support",
    requirements=[],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        ":kernel-support",  # not auto-inferred
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-agent",
        description="Backend.AI Agent",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "ag": "ai.backend.agent.cli:main",
            "ag.start-server": "ai.backend.agent.server:main",
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
        "py.typed",
    ],
)
