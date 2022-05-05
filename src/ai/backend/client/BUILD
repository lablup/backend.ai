python_sources(
    name="lib",
    dependencies=[
        "src/ai/backend/cli:lib",
        ":resources",
    ],
    sources=["**/*.py"],
)

python_distribution(
    name="dist",
    dependencies=[
        ":lib",
    ],
    provides=python_artifact(
        name="backend.ai-client",
        description="Backend.AI Client SDK",
        license="MIT",
    ),
    entry_points={
        "backendai_cli_v10": {
            "_": "ai.backend.client.cli.main:main",
        },
    },
    generate_setup=True,
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
