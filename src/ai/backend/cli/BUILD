python_sources(
    name="lib",
    dependencies=[
        "src/ai/backend/plugin:lib",
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
        name="backend.ai-cli",
        description="Backend.AI Command Line Interface Helper",
        license="MIT",
    ),
    entry_points={
        "console_scripts": {
            "backend.ai": "ai.backend.cli.__main__:main",
        },
    },
    generate_setup=True,
)

pex_binary(
    name="cli",
    dependencies=[
        ":lib",
    ],
    entry_point="ai.backend.cli.__main__:main",
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
