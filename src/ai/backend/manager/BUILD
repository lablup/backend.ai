python_sources(
    name="service",
    sources=["**/*.py"],
    dependencies=[
        "src/ai/backend/common:lib",
        ":resources",
    ],
)

pex_binary(
    name="server",
    dependencies=[
        ":service",
    ],
    entry_point="server.py",
    execution_mode="venv",
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
