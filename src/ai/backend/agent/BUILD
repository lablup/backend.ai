python_sources(
    name="service",
    sources=["**/*.py"],
    dependencies=[
        "src/ai/backend/cli:lib",
        "src/ai/backend/common:lib",
        "src/ai/backend/runner:lib",
        "src/ai/backend/helpers:lib",
        "src/ai/backend/kernel:lib",
        ":resources",
    ],
)

pex_binary(
    name="server",
    dependencies=[
        ":service",
    ],
    entry_point="server.py",
)

pex_binary(
    name="watcher",
    entry_point="watcher.py",
)

python_distribution(
    name="dist",
    dependencies=[
        ":service",
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
    repositories=[
        "@pypi",
    ],
)

resource(name="version", source="VERSION")

resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
        "docker/*.txt",
        "docker/*.tar.gz",
        "docker/*.bin",
        "kubernetes/*.txt",
        "kubernetes/*.tar.gz",
        "kubernetes/*.bin",
    ],
)
